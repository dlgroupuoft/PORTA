// Copyright 2021 The Casdoor Authors. All Rights Reserved.
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
func (application *Application) GetProviderByCategory(category string) (*Provider, error) {
func isProviderItemCountryCodeMatched(providerItem *ProviderItem, countryCode string) bool {
func (application *Application) GetProviderByCategoryAndRule(category string, method string, countryCode string) (*Provider, error) {
func (application *Application) GetEmailProvider(method string) (*Provider, error) {
func (application *Application) GetSmsProvider(method string, countryCode string) (*Provider, error) {
func (application *Application) GetStorageProvider() (*Provider, error) {
func (application *Application) getSignupItem(itemName string) *SignupItem {
func (application *Application) IsSignupItemVisible(itemName string) bool {
func (application *Application) IsSignupItemRequired(itemName string) bool {
func (si *SignupItem) isSignupItemPrompted() bool {
func (application *Application) GetSignupItemRule(itemName string) string {
func (application *Application) getAllPromptedProviderItems() []*ProviderItem {
func (application *Application) getAllPromptedSignupItems() []*SignupItem {
func (application *Application) isAffiliationPrompted() bool {
func (application *Application) HasPromptPage() bool {