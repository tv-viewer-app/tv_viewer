import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/utils/error_classification.dart';

void main() {
  group('isRecoverableImageDecodeError', () {
    test('recognizes known image decoding failures', () {
      expect(
        isRecoverableImageDecodeError(
          Exception('Could not decompress image.'),
        ),
        isTrue,
      );
      expect(
        isRecoverableImageDecodeError(
          Exception('Invalid image data'),
        ),
        isTrue,
      );
      expect(
        isRecoverableImageDecodeError(
          Exception('ImageCodecException: failed to decode image'),
        ),
        isTrue,
      );
    });

    test('does not suppress unrelated failures', () {
      expect(
        isRecoverableImageDecodeError(
          StateError('database unavailable'),
        ),
        isFalse,
      );
    });
  });
}
