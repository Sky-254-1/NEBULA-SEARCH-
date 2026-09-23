import { Camera, CameraResultType } from '@capacitor/camera';
import { Clipboard } from '@capacitor/clipboard';
import { Directory, Filesystem } from '@capacitor/filesystem';
import { Network } from '@capacitor/network';
import { Share } from '@capacitor/share';

export async function capturePhoto() {
  return Camera.getPhoto({ quality: 90, resultType: CameraResultType.Uri });
}

export async function copyToClipboard(text: string) {
  await Clipboard.write({ string: text });
}

export async function shareText(title: string, text: string) {
  await Share.share({ title, text });
}

export async function isOnline() {
  const status = await Network.getStatus();
  return status.connected;
}

export async function saveDownload(filename: string, data: string) {
  await Filesystem.writeFile({
    path: filename,
    data,
    directory: Directory.Documents,
  });
}
