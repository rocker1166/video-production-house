// Per-frame person matte for a whole video, via Vision person segmentation.
// usage: matte <in.mov> [balanced|accurate]  -> raw gray8 540x960 frames on stdout (pipe into ffmpeg)
// A sequence handler keeps the mask temporally stable, so edges don't shimmer frame to frame.
import Foundation
import AVFoundation
import Vision
import CoreImage

let args = CommandLine.arguments
guard args.count >= 2 else { FileHandle.standardError.write("usage: matte in.mov [balanced|accurate]\n".data(using: .utf8)!); exit(2) }
let quality: VNGeneratePersonSegmentationRequest.QualityLevel = (args.count > 2 && args[2] == "balanced") ? .balanced : .accurate
let W = 540, H = 960

let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
guard let track = asset.tracks(withMediaType: .video).first, let reader = try? AVAssetReader(asset: asset) else { exit(1) }
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(output)
reader.startReading()

let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = quality
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
let seq = VNSequenceRequestHandler()
let ctx = CIContext(options: [.workingColorSpace: NSNull()])
var buf = [UInt8](repeating: 0, count: W * H)
let out = FileHandle.standardOutput
var n = 0
while let sample = output.copyNextSampleBuffer(), let px = CMSampleBufferGetImageBuffer(sample) {
    try? seq.perform([request], on: px)
    if let mask = request.results?.first?.pixelBuffer {
        let m = CIImage(cvPixelBuffer: mask)
        let scaled = m.transformed(by: CGAffineTransform(scaleX: CGFloat(W) / m.extent.width, y: CGFloat(H) / m.extent.height))
        ctx.render(scaled, toBitmap: &buf, rowBytes: W, bounds: CGRect(x: 0, y: 0, width: W, height: H), format: .L8, colorSpace: nil)
    } else {
        buf = [UInt8](repeating: 0, count: W * H)   // keep frame count exact even if a frame fails
    }
    out.write(Data(buf))
    n += 1
}
FileHandle.standardError.write("matte frames: \(n)\n".data(using: .utf8)!)
