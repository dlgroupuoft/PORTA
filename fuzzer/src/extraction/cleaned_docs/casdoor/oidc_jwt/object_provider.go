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
type Provider struct {
func GetMaskedProvider(provider *Provider, isMaskEnabled bool) *Provider {
func GetMaskedProviders(providers []*Provider, isMaskEnabled bool) []*Provider {
func GetProviderCount(owner, field, value string) (int64, error) {
func GetGlobalProviderCount(field, value string) (int64, error) {
func GetProviders(owner string) ([]*Provider, error) {
func GetProvidersByCategory(owner string, category string) ([]*Provider, error) {
func GetGlobalProviders() ([]*Provider, error) {
func GetPaginationProviders(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Provider, error) {
func GetPaginationGlobalProviders(offset, limit int, field, value, sortField, sortOrder string) ([]*Provider, error) {
func getProvider(owner string, name string) (*Provider, error) {
func GetProvider(id string) (*Provider, error) {
func GetWechatMiniProgramProvider(application *Application) *Provider {
func UpdateProvider(id string, provider *Provider) (bool, error) {
func AddProvider(provider *Provider) (bool, error) {
func DeleteProvider(provider *Provider) (bool, error) {
func GetPaymentProvider(p *Provider) (pp.PaymentProvider, error) {
			// alipay provider store rootCert's name in metadata
func (p *Provider) GetId() string {
func GetCaptchaProviderByOwnerName(applicationId, lang string) (*Provider, error) {
func GetCaptchaProviderByApplication(applicationId, isCurrentProvider, lang string) (*Provider, error) {
			// For CAPTCHA providers, "None" means disabled (don't show CAPTCHA at all)
			// This is different from SMS/Email providers where "None" is treated as "All"
			// CAPTCHA Rule options are: "None" (disabled), "Dynamic", "Always", "Internet-Only"
func GetFaceIdProviderByOwnerName(applicationId, lang string) (*Provider, error) {
func GetFaceIdProviderByApplication(applicationId, isCurrentProvider, lang string) (*Provider, error) {
func GetIdvProviderByOwnerName(applicationId, lang string) (*Provider, error) {
func GetIdvProviderByApplication(applicationId, isCurrentProvider, lang string) (*Provider, error) {
func providerChangeTrigger(oldName string, newName string) error {
func FromProviderToIdpInfo(ctx *context.Context, provider *Provider) (*idp.ProviderInfo, error) {
		// For Alipay with certificate mode, load private key from certificate
func GetIdvProviderFromProvider(provider *Provider) idv.IdvProvider {