// Copyright 2025 The Casdoor Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
package object
func PlaceOrder(owner string, reqProductInfos []ProductInfo, user *User) (*Order, error) {
func PayOrder(providerName, host, paymentEnv string, order *Order, lang string) (payment *Payment, attachInfo map[string]interface{}, err error) {
	// For multi-product orders, the payment provider is determined by the first product
	// Create a subscription when pricing and plan are provided
	// This allows both free users and paid users to subscribe to plans
		// Check if plan restricts user to one subscription
	// Update order state first to avoid inconsistency
	// Update product stock after order state is persisted (for instant payment methods)
func CancelOrder(order *Order) (bool, error) {