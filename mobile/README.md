# BIST Katılım AI — Expo mobile preview

This is the first native iOS/Android preview of the existing BIST Katılım prediction dashboard. It reads the same public API and does not contain database keys or other service credentials.

## Run on a phone with Expo Go

1. Install the current **Expo Go** app from the official app store on the phone.
2. From this directory, run `npm install`.
3. Run `npx expo start --tunnel`.
4. Scan the displayed QR code with Expo Go on Android. On iPhone, scan it with the Camera app and open it in Expo Go.

If the app prompts for an Expo account on iPhone, sign in to Expo Go and the Expo CLI with the same account. See Expo's [device setup](https://docs.expo.dev/get-started/set-up-your-environment/) and [start developing](https://docs.expo.dev/get-started/start-developing/) guides.

The app has **Tahminler** and **Sonuç takibi** screens. It uses the current Render API endpoints for predictions and realized results. It is a development preview running inside Expo Go, not yet a signed App Store or Google Play release.
