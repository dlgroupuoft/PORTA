// Copyright 2022 The Casdoor Authors. All Rights Reserved.
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
type Payment struct {
	// Payment Provider Info
	// Product Info
	// Payer Info
	// Invoice Info
	// Order Info
func GetPaymentCount(owner, field, value string) (int64, error) {
func GetPayments(owner string) ([]*Payment, error) {
func GetUserPayments(owner, user string) ([]*Payment, error) {
func GetPaginationPayments(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Payment, error) {
func ExtendPaymentWithOrder(payments []*Payment) error {
func getPayment(owner string, name string) (*Payment, error) {
func GetPayment(id string) (*Payment, error) {
func UpdatePayment(id string, payment *Payment) (bool, error) {
func AddPayment(payment *Payment) (bool, error) {
func DeletePayment(payment *Payment) (bool, error) {
func notifyPayment(body []byte, owner string, paymentName string) (*Payment, *pp.NotifyResult, error) {
	// Check if the order products exist
	// Only check paid payment
func NotifyPayment(body []byte, owner string, paymentName string, lang string) (*Payment, error) {
	// Check if payment is already in a terminal state to prevent duplicate processing
	// Determine the new payment state
	// Check if the payment state would actually change
	// This prevents duplicate webhook events when providers send redundant notifications
	// Update order state based on payment status
		// Get provider, product and user for transaction creation
func invoicePayment(payment *Payment) (string, error) {
func InvoicePayment(payment *Payment) (string, error) {
func (payment *Payment) GetId() string {