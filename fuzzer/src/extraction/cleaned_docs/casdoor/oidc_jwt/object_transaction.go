// Copyright 2024 The Casdoor Authors. All Rights Reserved.
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
type TransactionCategory string
type Transaction struct {
func GetTransactionCount(owner, field, value string) (int64, error) {
func GetTransactions(owner string) ([]*Transaction, error) {
func GetUserTransactions(owner, user string) ([]*Transaction, error) {
func GetPaginationTransactions(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Transaction, error) {
func getTransaction(owner string, name string) (*Transaction, error) {
func GetTransaction(id string) (*Transaction, error) {
func UpdateTransaction(id string, transaction *Transaction, lang string) (bool, error) {
	// Revert old balance changes
	// Apply new balance changes
func AddTransaction(transaction *Transaction, lang string, dryRun bool) (bool, string, error) {
	// In dry run mode, only validate without making changes
func AddInternalPaymentTransaction(transaction *Transaction, lang string) (bool, error) {
	// Validate balance impact first
func AddExternalPaymentTransaction(transaction *Transaction, lang string) (bool, error) {
func DeleteTransaction(transaction *Transaction, lang string) (bool, error) {
	// Revert balance changes before deleting
func (transaction *Transaction) GetId() string {
func updateBalanceForTransaction(transaction *Transaction, amount float64, lang string) error {
		// Update organization's own balance
		// Update user's balance
		// Update organization's user balance sum