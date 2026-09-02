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
type CasServiceResponse struct {
type CasAuthenticationFailure struct {
type CasAuthenticationSuccess struct {
type CasProxies struct {
type CasAttributes struct {
type CasUserAttributes struct {
type CasNamedAttribute struct {
type CasAnyAttribute struct {
type CasAuthenticationSuccessWrapper struct {
type CasProxySuccess struct {
type CasProxyFailure struct {
type Saml11Request struct {
type Saml11AssertionArtifact struct {
// st is short for service ticket
// pgt is short for proxy granting ticket
func CheckCasLogin(application *Application, lang string, service string) error {
func StoreCasTokenForPgt(token *CasAuthenticationSuccess, service, userId string) string {
func GenerateId() {
// GetCasTokenByPgt
func GetCasTokenByPgt(pgt string) (bool, *CasAuthenticationSuccess, string, string) {
// GetCasTokenByTicket
func GetCasTokenByTicket(ticket string) (bool, *CasAuthenticationSuccess, string, string) {
func StoreCasTokenForProxyTicket(token *CasAuthenticationSuccess, targetService, userId string) string {
func escapeXMLText(input string) (string, error) {
func GenerateCasToken(userId string, service string) (string, error) {
// GetValidationBySaml
func GetValidationBySaml(samlRequest string, host string) (string, string, error) {
func (c *CasAuthenticationSuccess) DeepCopy() CasAuthenticationSuccess {
	// copy proxy
func (c *CasProxies) DeepCopy() CasProxies {
func (c *CasAttributes) DeepCopy() CasAttributes {
func (c *CasUserAttributes) DeepCopy() CasUserAttributes {