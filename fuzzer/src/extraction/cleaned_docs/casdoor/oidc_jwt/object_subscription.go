// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
type SubscriptionState string
type Subscription struct {
func (sub *Subscription) GetId() string {
func (sub *Subscription) UpdateState() error {
	// update subscription state by payment state
				// other states: Canceled, Timeout, Error
func NewSubscription(owner, userName, planName, paymentName, period string) (*Subscription, error) {
func GetSubscriptionCount(owner, field, value string) (int64, error) {
func GetSubscriptions(owner string) ([]*Subscription, error) {
func GetSubscriptionsByUser(owner, userName string) ([]*Subscription, error) {
	// update subscription state
func GetPaginationSubscriptions(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Subscription, error) {
func getSubscription(owner string, name string) (*Subscription, error) {
func GetSubscription(id string) (*Subscription, error) {
func HasActiveSubscriptionForPlan(owner, userName, planName string) (bool, error) {
		// Check if subscription is active, upcoming, or pending (not expired, error, or suspended)
func UpdateSubscription(id string, subscription *Subscription) (bool, error) {
func AddSubscription(subscription *Subscription) (bool, error) {
func DeleteSubscription(subscription *Subscription) (bool, error) {