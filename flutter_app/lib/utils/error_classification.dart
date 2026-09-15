bool isRecoverableImageDecodeError(Object error) {
  final message = error.toString().toLowerCase();
  return message.contains('could not decompress image') ||
      message.contains('invalid image data') ||
      message.contains('imagecodecexception') ||
      message.contains('failed to decode image');
}
