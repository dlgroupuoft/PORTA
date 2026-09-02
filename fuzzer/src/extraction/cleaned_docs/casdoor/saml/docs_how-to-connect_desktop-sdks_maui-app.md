---
title: .NET MAUI app
description: Integrate Casdoor in a .NET MAUI app (Android, Windows, etc.) with OpenID Connect.
keywords: [.NET, MAUI, SDK]
authors: [RVShershnev]
---

The [casdoor-dotnet-maui-example](https://github.com/RVShershnev/casdoor-dotnet-maui-example) includes a .NET MAUI app and library for Casdoor authentication via OpenID Connect.

## Demo

### Android

![Android](/img/how-to-connect/desktop-sdks/maui-app/android.gif)

### Windows

![Windows](/img/how-to-connect/desktop-sdks/maui-app/windows.gif)

## Requirements

- [.NET 7 SDK](https://dotnet.microsoft.com/download/dotnet/7.0)
- Target platform assets — see [MAUI first app](https://docs.microsoft.com/en-us/dotnet/maui/get-started/first-app)
- Visual Studio 2022 (Windows 17.3 or Mac 17.4) optional

## Get started

### 1. Create a MAUI app

Create a [MAUI application](https://docs.microsoft.com/en-us/dotnet/maui/get-started/first-app).

### 2. Add reference

Add a reference to `Casdoor.MauiOidcClient`.

### 3. Register the Casdoor client

Add `CasdoorClient` as a singleton in the services.

```csharp
builder.Services.AddSingleton(new CasdoorClient(new()
{
    Domain = "<your domain>",
    ClientId = "<your client>",
    Scope = "openid profile email",

#if WINDOWS
    RedirectUri = "http://localhost/callback"
#else
    RedirectUri = "casdoor://callback"
#endif
}));
```

### 4. UI (MainPage)

**MainPage.xaml**

```xml


```

**MainPage.cs**

```csharp
namespace Casdoor.MauiOidcClient.Example
{
    public partial class MainPage : ContentPage
    {
        int count = 0;
        private readonly CasdoorClient client;
        private string accessToken;
        public MainPage(CasdoorClient client)
        {
            InitializeComponent();
            this.client = client;

#if WINDOWS
    client.Browser = new WebViewBrowserAuthenticator(WebViewInstance);
#endif
        }

        private void OnCounterClicked(object sender, EventArgs e)
        {
            count++;

            if (count == 1)
                CounterBtn.Text = $"Clicked {count} time";
            else
                CounterBtn.Text = $"Clicked {count} times";

            SemanticScreenReader.Announce(CounterBtn.Text);
        }

        private async void OnLoginClicked(object sender, EventArgs e)
        {
            var loginResult = await client.LoginAsync();
            accessToken = loginResult.AccessToken;
            if (!loginResult.IsError)
            {
                NameLabel.Text = loginResult.User.Identity.Name;
                EmailLabel.Text = loginResult.User.Claims.FirstOrDefault(c => c.Type == "email")?.Value;            

                LoginView.IsVisible = false;
                HomeView.IsVisible = true;
            }
            else
            {
                await DisplayAlert("Error", loginResult.ErrorDescription, "OK");
            }
        }

        private async void OnLogoutClicked(object sender, EventArgs e)
        {
            var logoutResult = await client.LogoutAsync(accessToken);


            if (!logoutResult.IsError)
            {
                HomeView.IsVisible = false;
                LoginView.IsVisible = true;
                this.Focus();
            }
            else
            {
                await DisplayAlert("Error", logoutResult.ErrorDescription, "OK");
            }
        }
    }
}
```

### Step 5: Support the Android Platform

Modify the `AndroidManifest.xml` file.

```xml
```

### Step 6: Launch the Application

**Visual Studio:** Press Ctrl + F5 to start.
