// Validate a Live Photo WITHOUT touching the Photos library (no PHPhotoLibrary, no permission prompt).
//   validate <still> <video>   check A: PHLivePhoto.request(withResourceFileURLs:) builds a Live Photo from the pair
//   validate <NAME.pvt>        check A on the files inside + check B: the bundle, zipped the way a directory is
//                              shipped over AirDrop/drag-drop, decodes as PHLivePhoto via its NSItemProvider reader
//                              (PHLivePhoto's only readable type is com.apple.private.live-photo-bundle).
// Neither check looks at still-image-time, resolution or codec: passing is necessary, not sufficient.
import Foundation
import Photos
import AppKit
import UniformTypeIdentifiers

func checkPair(_ still: URL, _ video: URL) -> Bool {
  var finished = false, ok = false
  _ = PHLivePhoto.request(withResourceFileURLs: [still, video], placeholderImage: nil,
                          targetSize: .zero, contentMode: .aspectFit) { live, info in
    let degraded = (info[PHLivePhotoInfoIsDegradedKey] as? Bool) ?? false
    let err = info[PHLivePhotoInfoErrorKey] as? NSError
    if !degraded {
      ok = live != nil && err == nil; finished = true
      if let e = err { print("  A error: \(e.domain) \(e.code) \(e.localizedDescription)") }
    }
  }
  let deadline = Date().addingTimeInterval(20)
  while !finished && Date() < deadline { RunLoop.main.run(until: Date().addingTimeInterval(0.05)) }
  return ok
}

func checkBundle(_ pvt: URL) -> Bool {
  let type = (try? pvt.resourceValues(forKeys: [.contentTypeKey]))?.contentType?.identifier ?? "nil"
  print("  bundle UTI: \(type); PHLivePhoto readable types: \(PHLivePhoto.readableTypeIdentifiersForItemProvider)")
  guard type == "com.apple.private.live-photo-bundle" else { return false }
  let zip = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".zip")
  let p = Process()
  p.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
  p.arguments = ["-c", "-k", "--keepParent", pvt.path, zip.path]
  try? p.run(); p.waitUntilExit()
  defer { try? FileManager.default.removeItem(at: zip) }
  guard let data = try? Data(contentsOf: zip) else { return false }
  let cls: AnyClass = PHLivePhoto.self
  let sel = NSSelectorFromString("objectWithItemProviderData:typeIdentifier:error:")
  guard let m = class_getClassMethod(cls, sel) else { print("  B: reader not found"); return false }
  typealias F = @convention(c) (AnyObject, Selector, NSData, NSString, UnsafeMutablePointer<NSError?>?) -> AnyObject?
  let f = unsafeBitCast(method_getImplementation(m), to: F.self)
  var err: NSError?
  let obj = f(cls as AnyObject, sel, data as NSData, "com.apple.private.live-photo-bundle", &err)
  if let e = err { print("  B error: \(e.domain) \(e.code)") }
  return obj is PHLivePhoto
}

let a = CommandLine.arguments
var allOK = true
if a.count == 3 {
  let ok = checkPair(URL(fileURLWithPath: a[1]), URL(fileURLWithPath: a[2]))
  print("A pair  -> \(ok ? "PASS" : "FAIL")"); allOK = ok
} else if a.count == 2 {
  let pvt = URL(fileURLWithPath: a[1])
  let files = (try? FileManager.default.contentsOfDirectory(at: pvt, includingPropertiesForKeys: nil)) ?? []
  let still = files.first { ["heic", "jpg", "jpeg"].contains($0.pathExtension.lowercased()) }
  let video = files.first { $0.pathExtension.lowercased() == "mov" }
  let hasPlist = files.contains { $0.lastPathComponent == "metadata.plist" }
  print("  contents: \(files.map { $0.lastPathComponent }.sorted())")
  let okA = (still != nil && video != nil) ? checkPair(still!, video!) : false
  let okB = checkBundle(pvt)
  print("A pair   -> \(okA ? "PASS" : "FAIL")")
  print("B bundle -> \(okB ? "PASS" : "FAIL")\(hasPlist ? "" : " (no metadata.plist)")")
  allOK = okA && okB
} else { print("usage: validate still video | validate NAME.pvt"); exit(2) }
print(allOK ? "RESULT: VALID" : "RESULT: INVALID"); exit(allOK ? 0 : 1)
