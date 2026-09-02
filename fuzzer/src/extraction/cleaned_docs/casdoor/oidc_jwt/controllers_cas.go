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
package controllers
func queryUnescape(service string) string {
func (c *RootController) CasValidate() {
		// check whether service is the one for which we previously issued token
	// token not found
func (c *RootController) CasServiceValidate() {
func (c *RootController) CasProxyValidate() {
	// https://apereo.github.io/cas/6.6.x/protocol/CAS-Protocol-Specification.html#26-proxyvalidate-cas-20
	// "/proxyValidate" should accept both service tickets and proxy tickets.
func (c *RootController) CasP3ServiceValidate() {
func (c *RootController) CasP3ProxyValidate() {
	// check whether all required parameters are met
	// find the token
		// check whether service is the one for which we previously issued token
			// service not match
		// token not found
		// that means we are in proxy web flow
		// todo: check whether it is https
		// make a request to pgturl passing pgt and pgtiou
			// failed to send request
	// everything is ok, send the response
func (c *RootController) CasProxy() {
func (c *RootController) SamlValidate() {
func (c *RootController) sendCasProxyResponseErr(code, msg, format string) {
func (c *RootController) sendCasAuthenticationResponseErr(code, msg, format string) {