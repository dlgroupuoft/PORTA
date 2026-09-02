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
func ParseSamlResponse(samlResponse string, provider *Provider, host string) (*idp.UserInfo, error) {
	// Fallback: if Username is empty, use Email or NameID
func GenerateSamlRequest(id, relayState, host, lang string) (auth string, method string, err error) {
func buildSp(provider *Provider, samlResponse string, host string) (*saml2.SAMLServiceProvider, error) {
func buildSpKeyStore() (dsig.X509KeyStore, error) {
func buildSpCertificateStore(provider *Provider, samlResponse string) (certStore dsig.MemoryX509CertificateStore, err error) {
		// this was a PEM file
		// block.Bytes are DER encoded so the following code block should happily accept it
func getCertificateFromSamlResponse(samlResponse string, providerType string) (string, error) {
		// <ds:X509Certificate>...</ds:X509Certificate>
		// <dsig:X509Certificate>...</dsig:X509Certificate>
		// <X509Certificate>...</X509Certificate>
		// ...