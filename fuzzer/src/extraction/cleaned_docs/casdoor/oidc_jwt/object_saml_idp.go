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
// NewSamlResponse
// returns a saml2 response
func NewSamlResponse(application *Application, user *User, host string, certificate string, destination string, iss string, requestId string, redirectUri []string) (*etree.Element, error) {
	// Add redirect URIs as audiences, but skip duplicates and empty values
type X509Key struct {
func (x X509Key) GetKeyPair() (privateKey *rsa.PrivateKey, cert []byte, err error) {
// IdpEntityDescriptor
// SAML METADATA
type IdpEntityDescriptor struct {
type KeyInfo struct {
type X509Data struct {
type X509Certificate struct {
type KeyDescriptor struct {
type IdpSSODescriptor struct {
type NameIDFormat struct {
	// XMLName xml.Name
type SingleSignOnService struct {
	// XMLName  xml.Name
type Attribute struct {
	// XMLName      xml.Name
func GetSamlMeta(application *Application, host string, enablePostBinding bool) (*IdpEntityDescriptor, error) {
// GetSamlResponse generates a SAML2.0 response
// parameter samlRequest is saml request in base64 format
func GetSamlResponse(application *Application, user *User, samlRequest string, host string) (string, string, string, error) {
	// request type
	// base64 decode
		// decompress
	// verify samlRequest
	// get certificate string
	// redirect Url (Assertion Consumer Url)
	// build signedResponse
	// signedXML, err := ctx.SignEnvelopedLimix(samlResponse)
	// if err != nil {
	//	return "", "", fmt.Errorf("err: %s", err.Error())
	// }
	// Sign the assertion (SAML 2.0 best practice)
	// Only sign if EnableSamlAssertionSignature is true
			// Insert signature as the second child of assertion (after Issuer)
	// Sign the response
	// Write to bytes
	// compress
	// base64 encode
// NewSamlResponse11 return a saml1.1 response(not 2.0)
func NewSamlResponse11(application *Application, user *User, requestID string, host string) (*etree.Element, error) {
	// create assertion which is inside the response
	// AuthenticationStatement inside assertion
	// subject inside AuthenticationStatement
	// nameIdentifier inside subject
	// nameIdentifier.CreateAttr("Format", "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress")
	// subjectConfirmation inside subject
func GetSamlRedirectAddress(owner string, application string, relayState string, samlRequest string, host string, username string, loginHint string) string {