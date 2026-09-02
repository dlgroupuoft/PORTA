---
title: PayPal payment
description: Use PayPal as a payment provider in Casdoor.
keywords: [PayPal, payment]
authors: [Chinoholo0807]
---

## 1. Create a PayPal app

You need a **PayPal business account**. [Create one](https://www.paypal.com/in/webapps/mpp/account-selection?pros=2) if needed, then sign in to the [Developer Dashboard](https://developer.paypal.com/dashboard/applications/sandbox) and click **Create App** under **Apps & Credentials**.

Copy the **Client ID** and **Secret** from the app’s basic information.

![create a PayPal application](/img/providers/payment/paypal_create_app.png)
![PayPal application details](/img/providers/payment/paypal_app_detail.png)

## 2. Create the provider in Casdoor

Add a **Payment** provider, set **Type** to **PayPal**, and enter the **Client ID** and **Secret** (Client secret).

## 3. Attach to your product

Add the PayPal provider to your product so users can pay with PayPal.

![add PayPal payment provider for product](/img/providers/payment/paypal_product.png)
