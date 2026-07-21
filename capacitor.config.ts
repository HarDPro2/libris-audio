import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.librisaudio.app',
  appName: 'Libris Audio',
  webDir: 'dist',
  // When running in a native WebView, use the server URL for hot reload in dev.
  // In production builds this block is ignored.
  server: {
    androidScheme: 'https',
  },
  android: {
    // Allow the app to load the Render backend from a non-localhost URL
    allowMixedContent: true,
    // Build a release-ready APK
    buildOptions: {
      releaseType: 'APK',
    },
  },
  plugins: {
    BackgroundRunner: {
      label: 'com.librisaudio.background',
      src: 'background.js',
      event: 'keepAlive',
      repeat: true,
      interval: 14,                  // minutes — matches your existing ping interval
      autoStart: false,
    },
  },
};

export default config;
