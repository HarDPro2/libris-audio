/**
 * Background Runner script for Libris Audio.
 * This runs in a native Android background thread (BackgroundRunner plugin).
 * Its purpose is to keep the app process alive and send a keepAlive ping
 * every 14 minutes so the OS doesn't kill the audio foreground service.
 */
addEventListener('keepAlive', async (resolve, reject, args) => {
  try {
    // The BackgroundRunner keeps the app's process alive.
    // The actual audio playback is handled natively by the WebView's audio element
    // which is connected to a Foreground Service declared in AndroidManifest.xml.
    console.log('[BackgroundRunner] keepAlive tick - audio service is running');
    resolve();
  } catch (err) {
    reject(err);
  }
});
