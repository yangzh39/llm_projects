#import <AppKit/AppKit.h>
#import <AVFoundation/AVFoundation.h>
#import <CoreVideo/CoreVideo.h>
#import <Foundation/Foundation.h>

static CVPixelBufferRef CreatePixelBuffer(NSURL *url, int width, int height) {
    NSImage *image = [[NSImage alloc] initWithContentsOfURL:url];
    if (!image) return NULL;
    NSRect proposed = NSMakeRect(0, 0, width, height);
    CGImageRef cgImage = [image CGImageForProposedRect:&proposed context:nil hints:nil];
    if (!cgImage) return NULL;

    NSDictionary *attrs = @{
        (NSString *)kCVPixelBufferCGImageCompatibilityKey: @YES,
        (NSString *)kCVPixelBufferCGBitmapContextCompatibilityKey: @YES,
    };
    CVPixelBufferRef buffer = NULL;
    CVReturn result = CVPixelBufferCreate(kCFAllocatorDefault, width, height,
                                           kCVPixelFormatType_32ARGB,
                                           (__bridge CFDictionaryRef)attrs, &buffer);
    if (result != kCVReturnSuccess || !buffer) return NULL;

    CVPixelBufferLockBaseAddress(buffer, 0);
    CGContextRef context = CGBitmapContextCreate(
        CVPixelBufferGetBaseAddress(buffer), width, height, 8,
        CVPixelBufferGetBytesPerRow(buffer), CGColorSpaceCreateDeviceRGB(),
        kCGImageAlphaNoneSkipFirst);
    if (!context) {
        CVPixelBufferUnlockBaseAddress(buffer, 0);
        CVPixelBufferRelease(buffer);
        return NULL;
    }
    CGContextSetRGBFillColor(context, 1, 1, 1, 1);
    CGContextFillRect(context, CGRectMake(0, 0, width, height));
    CGContextDrawImage(context, CGRectMake(0, 0, width, height), cgImage);
    CGContextRelease(context);
    CVPixelBufferUnlockBaseAddress(buffer, 0);
    return buffer;
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 3) {
            fprintf(stderr, "Usage: encode_slideshow <frames_dir> <output.mp4>\n");
            return 2;
        }
        NSString *framesPath = [NSString stringWithUTF8String:argv[1]];
        NSString *outputPath = [NSString stringWithUTF8String:argv[2]];
        NSFileManager *fm = [NSFileManager defaultManager];
        NSError *error = nil;
        NSArray<NSString *> *names = [fm contentsOfDirectoryAtPath:framesPath error:&error];
        if (!names) {
            fprintf(stderr, "Cannot list frames: %s\n", error.localizedDescription.UTF8String);
            return 3;
        }
        NSPredicate *predicate = [NSPredicate predicateWithBlock:^BOOL(NSString *name, NSDictionary *bindings) {
            return [name hasPrefix:@"scene_"] && [[name pathExtension].lowercaseString isEqualToString:@"png"];
        }];
        names = [[names filteredArrayUsingPredicate:predicate] sortedArrayUsingSelector:@selector(compare:)];

        NSString *durationsText = [NSString stringWithContentsOfFile:[framesPath stringByAppendingPathComponent:@"durations.txt"]
                                                            encoding:NSUTF8StringEncoding error:&error];
        if (!durationsText) {
            fprintf(stderr, "Cannot read durations: %s\n", error.localizedDescription.UTF8String);
            return 4;
        }
        NSMutableArray<NSNumber *> *durations = [NSMutableArray array];
        for (NSString *line in [durationsText componentsSeparatedByCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]]) {
            if (line.length) [durations addObject:@(line.integerValue)];
        }
        if (names.count == 0 || names.count != durations.count) {
            fprintf(stderr, "Frame and duration counts do not match.\n");
            return 5;
        }

        [fm removeItemAtPath:outputPath error:nil];
        NSURL *outputURL = [NSURL fileURLWithPath:outputPath];
        AVAssetWriter *writer = [[AVAssetWriter alloc] initWithURL:outputURL fileType:AVFileTypeMPEG4 error:&error];
        if (!writer) {
            fprintf(stderr, "Cannot create writer: %s\n", error.localizedDescription.UTF8String);
            return 6;
        }
        const int width = 1920, height = 1080;
        const int32_t fps = 30;
        NSDictionary *compression = @{
            AVVideoAverageBitRateKey: @5000000,
            AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
        };
        NSDictionary *settings = @{
            AVVideoCodecKey: AVVideoCodecTypeH264,
            AVVideoWidthKey: @(width),
            AVVideoHeightKey: @(height),
            AVVideoCompressionPropertiesKey: compression,
        };
        AVAssetWriterInput *input = [[AVAssetWriterInput alloc] initWithMediaType:AVMediaTypeVideo outputSettings:settings];
        input.expectsMediaDataInRealTime = NO;
        NSDictionary *sourceAttrs = @{
            (NSString *)kCVPixelBufferPixelFormatTypeKey: @(kCVPixelFormatType_32ARGB),
            (NSString *)kCVPixelBufferWidthKey: @(width),
            (NSString *)kCVPixelBufferHeightKey: @(height),
        };
        AVAssetWriterInputPixelBufferAdaptor *adaptor =
            [[AVAssetWriterInputPixelBufferAdaptor alloc] initWithAssetWriterInput:input
                                                        sourcePixelBufferAttributes:sourceAttrs];
        if (![writer canAddInput:input]) {
            fprintf(stderr, "Cannot add video input.\n");
            return 7;
        }
        [writer addInput:input];
        if (![writer startWriting]) {
            fprintf(stderr, "Cannot start writer: %s\n", writer.error.localizedDescription.UTF8String);
            return 8;
        }
        [writer startSessionAtSourceTime:kCMTimeZero];

        int64_t frameIndex = 0;
        for (NSUInteger scene = 0; scene < names.count; scene++) {
            NSURL *imageURL = [NSURL fileURLWithPath:[framesPath stringByAppendingPathComponent:names[scene]]];
            CVPixelBufferRef buffer = CreatePixelBuffer(imageURL, width, height);
            if (!buffer) {
                fprintf(stderr, "Cannot create pixel buffer for %s\n", imageURL.path.UTF8String);
                return 9;
            }
            NSInteger repeat = durations[scene].integerValue * fps;
            for (NSInteger i = 0; i < repeat; i++) {
                while (!input.readyForMoreMediaData) [NSThread sleepForTimeInterval:0.005];
                CMTime time = CMTimeMake(frameIndex, fps);
                if (![adaptor appendPixelBuffer:buffer withPresentationTime:time]) {
                    fprintf(stderr, "Append failed: %s\n", writer.error.localizedDescription.UTF8String);
                    CVPixelBufferRelease(buffer);
                    return 10;
                }
                frameIndex++;
            }
            CVPixelBufferRelease(buffer);
            printf("Encoded scene %lu/%lu\n", (unsigned long)(scene + 1), (unsigned long)names.count);
        }

        [input markAsFinished];
        dispatch_semaphore_t semaphore = dispatch_semaphore_create(0);
        [writer finishWritingWithCompletionHandler:^{ dispatch_semaphore_signal(semaphore); }];
        dispatch_semaphore_wait(semaphore, DISPATCH_TIME_FOREVER);
        if (writer.status != AVAssetWriterStatusCompleted) {
            fprintf(stderr, "Encoding failed: %s\n", writer.error.localizedDescription.UTF8String);
            return 11;
        }
        printf("Created %s\n", outputPath.UTF8String);
    }
    return 0;
}
