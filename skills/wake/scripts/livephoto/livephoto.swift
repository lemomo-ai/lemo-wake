// lemo-wake: make an Apple Live Photo from a still image + a short video.
//
// Usage:
//   livephoto <still.(png|jpg|heic)> <video.(mov|mp4)> <out-dir> <NAME> [--key SEC] [--duration SEC]
//             [--max-side PX] [--jpeg] [--h264]
//
// Writes into <out-dir>:
//   NAME.HEIC (or NAME.JPG)  still, Apple MakerNote tag 17 = content identifier
//   NAME.MOV                 video: mdta com.apple.quicktime.content.identifier (same UUID) +
//                            timed metadata track (mebx) com.apple.quicktime.still-image-time = -1 at --key
//   NAME.pvt/                Live Photo bundle (UTI com.apple.private.live-photo-bundle) holding copies of
//                            the two files + metadata.plist. THIS is what to AirDrop: a loose HEIC+MOV pair
//                            is sent as two unrelated items and the iPhone saves a photo and a video.
//
// Defaults: --key 0 (the still should be the frame shown at that time), --duration 3, --max-side 1920.
import AVFoundation
import CoreMedia
import Foundation
import ImageIO
import UniformTypeIdentifiers

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }
func num(_ s: String?, _ flag: String) -> Double { if let s = s, let v = Double(s) { return v }; fail("bad \(flag)") }

var pos: [String] = []
var keySeconds = 0.0, duration = 3.0, maxSide = 1920.0, useJPEG = false, useH264 = false
var it = CommandLine.arguments.dropFirst().makeIterator()
while let a = it.next() {
  switch a {
  case "--key": keySeconds = num(it.next(), "--key")
  case "--duration": duration = num(it.next(), "--duration")
  case "--max-side": maxSide = num(it.next(), "--max-side")
  case "--jpeg": useJPEG = true
  case "--h264": useH264 = true
  default: pos.append(a)
  }
}
guard pos.count == 4 else {
  print("usage: livephoto still video out-dir NAME [--key SEC] [--duration SEC] [--max-side PX] [--jpeg] [--h264]"); exit(2)
}
let stillURL = URL(fileURLWithPath: pos[0]), videoURL = URL(fileURLWithPath: pos[1])
let outDir = URL(fileURLWithPath: pos[2], isDirectory: true), name = pos[3]
let fm = FileManager.default
try? fm.createDirectory(at: outDir, withIntermediateDirectories: true)
let imgExt = useJPEG ? "JPG" : "HEIC"
let imgURL = outDir.appendingPathComponent("\(name).\(imgExt)")
let movURL = outDir.appendingPathComponent("\(name).MOV")
let pvtURL = outDir.appendingPathComponent("\(name).pvt", isDirectory: true)
for u in [imgURL, movURL, pvtURL] { try? fm.removeItem(at: u) }
let assetID = UUID().uuidString

// ---------- 1. still ----------
guard let src = CGImageSourceCreateWithURL(stillURL as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { fail("cannot read still") }
let stillW = Double(cg.width), stillH = Double(cg.height)
guard let dest = CGImageDestinationCreateWithURL(imgURL as CFURL,
        (useJPEG ? UTType.jpeg : UTType.heic).identifier as CFString, 1, nil) else { fail("cannot create image") }
let imgProps: [CFString: Any] = [
  kCGImagePropertyMakerAppleDictionary: ["17": assetID],
  kCGImageDestinationLossyCompressionQuality: 0.92,
  kCGImagePropertyOrientation: 1,
]
CGImageDestinationAddImage(dest, cg, imgProps as CFDictionary)
guard CGImageDestinationFinalize(dest) else { fail("image write failed") }
// verify the maker note survived ImageIO
if let chk = CGImageSourceCreateWithURL(imgURL as CFURL, nil),
   let p = CGImageSourceCopyPropertiesAtIndex(chk, 0, nil) as? [CFString: Any],
   let mk = p[kCGImagePropertyMakerAppleDictionary] as? [String: Any], (mk["17"] as? String) == assetID {
} else { fail("maker note 17 missing after write") }

// ---------- 2. movie ----------
let asset = AVURLAsset(url: videoURL)
guard let track = asset.tracks(withMediaType: .video).first else { fail("no video track") }
let natural = track.naturalSize.applying(track.preferredTransform)
let srcW = abs(natural.width), srcH = abs(natural.height)
let srcAR = srcW / srcH, stillAR = stillW / stillH
if abs(srcAR - stillAR) / stillAR > 0.01 {
  print("WARNING: video aspect \(srcAR) != still aspect \(stillAR); Live Photo will look cropped/jumpy")
}
// fit inside maxSide, keep aspect, even dimensions
let scale = min(1.0, maxSide / Double(max(srcW, srcH)))
func even(_ v: Double) -> Int { max(2, Int((v / 2).rounded()) * 2) }
let outW = even(Double(srcW) * scale), outH = even(Double(srcH) * scale)
let srcDur = CMTimeGetSeconds(asset.duration)
let clipDur = min(duration, srcDur)
if keySeconds < 0 || keySeconds > clipDur { fail("--key \(keySeconds) outside clip 0...\(clipDur)") }

let reader = try AVAssetReader(asset: asset)
reader.timeRange = CMTimeRange(start: .zero, duration: CMTime(seconds: clipDur, preferredTimescale: 600))
// a video composition applies preferredTransform and scales to the output size
let comp = AVMutableVideoComposition(propertiesOf: asset)
comp.renderSize = CGSize(width: outW, height: outH)
let fps = track.nominalFrameRate > 0 ? Double(track.nominalFrameRate) : 30
comp.frameDuration = CMTime(value: 1, timescale: CMTimeScale(fps.rounded()))
let instr = AVMutableVideoCompositionInstruction()
instr.timeRange = CMTimeRange(start: .zero, duration: asset.duration)
let layer = AVMutableVideoCompositionLayerInstruction(assetTrack: track)
let sx = CGFloat(outW) / srcW, sy = CGFloat(outH) / srcH
var t = track.preferredTransform
// move rotated content back to origin, then scale
let r = CGRect(origin: .zero, size: track.naturalSize).applying(t)
t = t.concatenating(CGAffineTransform(translationX: -r.minX, y: -r.minY)).concatenating(CGAffineTransform(scaleX: sx, y: sy))
layer.setTransform(t, at: .zero)
instr.layerInstructions = [layer]
comp.instructions = [instr]
let vout = AVAssetReaderVideoCompositionOutput(videoTracks: [track],
  videoSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
vout.videoComposition = comp
reader.add(vout)

let writer = try AVAssetWriter(outputURL: movURL, fileType: .mov)
let bitrate = Int(Double(outW * outH) * fps * 0.12)  // ~7-10 Mbps at 1080p30
let videoIn = AVAssetWriterInput(mediaType: .video, outputSettings: [
  AVVideoCodecKey: useH264 ? AVVideoCodecType.h264 : AVVideoCodecType.hevc,
  AVVideoWidthKey: outW, AVVideoHeightKey: outH,
  AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: bitrate],
])
videoIn.expectsMediaDataInRealTime = false
writer.add(videoIn)

// timed metadata track: still-image-time (int8). Apple's camera always writes -1; the TIME of the sample marks the key frame.
let spec: [String: Any] = [
  kCMMetadataFormatDescriptionMetadataSpecificationKey_Identifier as String: "mdta/com.apple.quicktime.still-image-time",
  kCMMetadataFormatDescriptionMetadataSpecificationKey_DataType as String: "com.apple.metadata.datatype.int8",
]
var formatDesc: CMFormatDescription?
CMMetadataFormatDescriptionCreateWithMetadataSpecifications(allocator: kCFAllocatorDefault,
  metadataType: kCMMetadataFormatType_Boxed, metadataSpecifications: [spec] as CFArray, formatDescriptionOut: &formatDesc)
let metaIn = AVAssetWriterInput(mediaType: .metadata, outputSettings: nil, sourceFormatHint: formatDesc)
let adaptor = AVAssetWriterInputMetadataAdaptor(assetWriterInput: metaIn)
writer.add(metaIn)
if metaIn.canAddTrackAssociation(withTrackOf: videoIn, type: AVAssetTrack.AssociationType.metadataReferent.rawValue) {
  metaIn.addTrackAssociation(withTrackOf: videoIn, type: AVAssetTrack.AssociationType.metadataReferent.rawValue)
}

let idItem = AVMutableMetadataItem()
idItem.keySpace = .quickTimeMetadata
idItem.key = "com.apple.quicktime.content.identifier" as NSString
idItem.value = assetID as NSString
idItem.dataType = "com.apple.metadata.datatype.UTF-8"
writer.metadata = [idItem]

guard writer.startWriting() else { fail("writer start: \(String(describing: writer.error))") }
guard reader.startReading() else { fail("reader start: \(String(describing: reader.error))") }
writer.startSession(atSourceTime: .zero)

let stillItem = AVMutableMetadataItem()
stillItem.keySpace = .quickTimeMetadata
stillItem.key = "com.apple.quicktime.still-image-time" as NSString
stillItem.value = NSNumber(value: Int8(-1))
stillItem.dataType = "com.apple.metadata.datatype.int8"
let keyTime = CMTime(seconds: keySeconds, preferredTimescale: 600)
adaptor.append(AVTimedMetadataGroup(items: [stillItem],
  timeRange: CMTimeRange(start: keyTime, duration: CMTime(value: 20, timescale: 600))))
metaIn.markAsFinished()

var frames = 0
let end = CMTime(seconds: clipDur, preferredTimescale: 600)
while let sample = vout.copyNextSampleBuffer() {
  if CMSampleBufferGetPresentationTimeStamp(sample) >= end { break }
  while !videoIn.isReadyForMoreMediaData { usleep(2000) }
  if !videoIn.append(sample) { fail("append failed: \(String(describing: writer.error))") }
  frames += 1
}
reader.cancelReading()
videoIn.markAsFinished()
writer.endSession(atSourceTime: end)
let sem = DispatchSemaphore(value: 0)
writer.finishWriting { sem.signal() }
sem.wait()
guard writer.status == .completed else { fail("write failed: \(String(describing: writer.error))") }

// ---------- 3. .pvt bundle (what AirDrop / drag-drop / share sheets treat as ONE Live Photo) ----------
try fm.createDirectory(at: pvtURL, withIntermediateDirectories: true)
try fm.copyItem(at: imgURL, to: pvtURL.appendingPathComponent(imgURL.lastPathComponent))
try fm.copyItem(at: movURL, to: pvtURL.appendingPathComponent(movURL.lastPathComponent))
let plist: [String: Any] = ["PFVideoComplementMetadataVersionKey": "1"]
let plistData = try PropertyListSerialization.data(fromPropertyList: plist, format: .xml, options: 0)
try plistData.write(to: pvtURL.appendingPathComponent("metadata.plist"))

print("ok id=\(assetID) still=\(Int(stillW))x\(Int(stillH)) video=\(outW)x\(outH) \(frames)f \(String(format: "%.2f", clipDur))s key=\(keySeconds)s codec=\(useH264 ? "h264" : "hevc")")
print("  \(imgURL.path)\n  \(movURL.path)\n  \(pvtURL.path)")
