import AppKit
import AVFoundation
import CoreVideo
import Foundation

guard CommandLine.arguments.count == 3 else {
    fputs("Usage: swift encode_slideshow.swift <frames_dir> <output.mp4>\n", stderr)
    exit(2)
}

let framesDir = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
let fileManager = FileManager.default

let imageURLs = try fileManager.contentsOfDirectory(at: framesDir, includingPropertiesForKeys: nil)
    .filter { $0.lastPathComponent.hasPrefix("scene_") && $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }

let durationsText = try String(contentsOf: framesDir.appendingPathComponent("durations.txt"))
let durations = durationsText.split(whereSeparator: \.isWhitespace).compactMap { Int($0) }

guard !imageURLs.isEmpty, imageURLs.count == durations.count else {
    fputs("Frame and duration counts do not match.\n", stderr)
    exit(3)
}

try? fileManager.removeItem(at: outputURL)

let width = 1920
let height = 1080
let fps: Int32 = 30
let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mp4)
let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 5_000_000,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel
    ]
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
input.expectsMediaDataInRealTime = false
let attributes: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32ARGB),
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height
]
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attributes)
guard writer.canAdd(input) else {
    fputs("Cannot add video input.\n", stderr)
    exit(4)
}
writer.add(input)

func makePixelBuffer(from url: URL) -> CVPixelBuffer? {
    guard let nsImage = NSImage(contentsOf: url) else { return nil }
    var proposed = CGRect(x: 0, y: 0, width: width, height: height)
    guard let cgImage = nsImage.cgImage(forProposedRect: &proposed, context: nil, hints: nil) else { return nil }

    var buffer: CVPixelBuffer?
    let status = CVPixelBufferCreate(
        kCFAllocatorDefault,
        width,
        height,
        kCVPixelFormatType_32ARGB,
        attributes as CFDictionary,
        &buffer
    )
    guard status == kCVReturnSuccess, let pixelBuffer = buffer else { return nil }
    CVPixelBufferLockBaseAddress(pixelBuffer, [])
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, []) }

    guard let context = CGContext(
        data: CVPixelBufferGetBaseAddress(pixelBuffer),
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: CVPixelBufferGetBytesPerRow(pixelBuffer),
        space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
    ) else { return nil }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.translateBy(x: 0, y: CGFloat(height))
    context.scaleBy(x: 1, y: -1)
    context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
    return pixelBuffer
}

guard writer.startWriting() else {
    fputs("Could not start writer: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
    exit(5)
}
writer.startSession(atSourceTime: .zero)

var frameIndex: Int64 = 0
for (sceneIndex, imageURL) in imageURLs.enumerated() {
    guard let pixelBuffer = makePixelBuffer(from: imageURL) else {
        fputs("Could not load \(imageURL.path)\n", stderr)
        exit(6)
    }
    let repeatedFrames = durations[sceneIndex] * Int(fps)
    for _ in 0..<repeatedFrames {
        while !input.isReadyForMoreMediaData {
            Thread.sleep(forTimeInterval: 0.005)
        }
        let time = CMTime(value: frameIndex, timescale: fps)
        guard adaptor.append(pixelBuffer, withPresentationTime: time) else {
            fputs("Append failed: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
            exit(7)
        }
        frameIndex += 1
    }
    print("Encoded scene \(sceneIndex + 1)/\(imageURLs.count)")
}

input.markAsFinished()
let semaphore = DispatchSemaphore(value: 0)
writer.finishWriting { semaphore.signal() }
semaphore.wait()

guard writer.status == .completed else {
    fputs("Encoding failed: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
    exit(8)
}

print("Created \(outputURL.path)")
