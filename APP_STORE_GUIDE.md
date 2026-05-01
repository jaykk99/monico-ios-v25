# APP_STORE_GUIDE.md

This guide outlines the steps for testing your Monico-iOS application on an iPhone and subsequently submitting it to the Apple App Store.

## Phase 2: iPhone Testing (This Week - 1-2 hours)

Before submitting your app to the App Store, it is crucial to thoroughly test it on a physical iPhone device. This phase ensures that the app functions as expected in a real-world environment.

### Step 1: Connect iPhone and Enable Developer Mode

Connect your iPhone to your computer. Ensure that Developer Mode is enabled on your iPhone. You can usually find this setting in `Settings > Privacy & Security > Developer Mode`.

### Step 2: Build and Run on Device

Use the Briefcase tool to build and run your application directly on your connected iPhone. This command will compile your app and deploy it to the device.

```bash
briefcase build ios --device
briefcase run ios --device
```

*   `briefcase build ios --device`: This command builds the iOS application specifically for a connected device.
*   `briefcase run ios --device`: This command runs the built application on the connected device.

### Step 3: Test Everything Works ✅

Once the app is running on your iPhone, perform comprehensive testing. Verify all functionalities, user interface elements, and ensure there are no crashes or unexpected behaviors. Pay close attention to:

*   **User Interface**: Ensure all elements are displayed correctly and are responsive.
*   **Functionality**: Test all features and interactions within the app.
*   **Performance**: Check for smooth scrolling, quick loading times, and overall responsiveness.
*   **Error Handling**: Verify that the app handles errors gracefully.

## Phase 3: App Store Submission (Next Week - 2-3 hours)

After successful testing on your iPhone, you can proceed with preparing your app for submission to the Apple App Store. This involves creating a release build and using App Store Connect for the submission process.

### Step 1: Build Release Version

Create a release build of your application. This build will be optimized for distribution and will include all necessary components for App Store submission.

```bash
briefcase build ios --release
```

*   `briefcase build ios --release`: This command creates a release-ready build of your iOS application, typically generating an `.ipa` file.

### Step 2: Create App Store Connect App

Log in to [App Store Connect](https://appstoreconnect.apple.com/) and create a new app entry. You will need to provide basic information about your app, such as its name, bundle ID, and primary language.

### Step 3: Upload Screenshots, Metadata, Icon

Prepare and upload all required assets and information to your app entry in App Store Connect. This includes:

*   **Screenshots**: High-quality screenshots of your app running on various device sizes.
*   **Metadata**: App description, keywords, support URL, marketing URL, and privacy policy URL.
*   **Icon**: Your app's icon in various required sizes.

### Step 4: Submit for Review

Once all information and assets are uploaded, submit your app for review. Apple's review team will assess your app against their App Store Review Guidelines. This process can take a few days.

### Step 5: Done! App Goes Live in 24-48 hours 🎉

After your app passes the review, it will be approved and made available on the App Store. Typically, it takes 24-48 hours for the app to go live after approval.
