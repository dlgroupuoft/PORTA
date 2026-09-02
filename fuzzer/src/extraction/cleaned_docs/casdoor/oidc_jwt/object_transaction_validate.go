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
func validateBalanceForTransaction(transaction *Transaction, amount float64, lang string) error {
		// Validate organization balance change
		// Validate user balance change
		// Validate organization's user balance sum change
func validateOrganizationBalance(owner string, name string, balance float64, currency string, isOrgBalance bool, lang string) error {
	// Convert the balance amount from transaction currency to organization's balance currency
		// Check organization balance credit limit
		// User balance is just a sum of all users' balances, no credit limit check here
		// Individual user credit limits are checked in validateUserBalance
	// In validation mode, we don't actually update the balance
func validateUserBalance(owner string, name string, balance float64, currency string, lang string) error {
	// Convert the balance amount from transaction currency to user's balance currency
		// Get organization's balance currency as fallback
	// Calculate new balance
	// Check balance credit limit
	// User.BalanceCredit takes precedence over Organization.BalanceCredit
		// Get organization's balance credit as fallback
	// Validate new balance against credit limit
	// In validation mode, we don't actually update the balance