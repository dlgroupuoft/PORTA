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
// Casdoor will expose its providers as services to SDK
// We are going to implement those services as APIs here
package controllers
type EmailForm struct {
type SmsForm struct {
type NotificationForm struct {
// SendEmail
// @Title SendEmail
// @Tag Service API
// @Description This API is not for Casdoor frontend to call, it is for Casdoor SDKs.
// @Param   clientId    query    string  true        "The clientId of the application"
// @Param   clientSecret    query    string  true    "The clientSecret of the application"
// @Param   from    body   controllers.EmailForm    true         "Details of the email request"
// @Success 200 {object} controllers.Response The Response object
// @router /send-email [post]
func (c *ApiController) SendEmail() {
		// called by frontend's TestEmailWidget, provider name is set by frontend
		// called by Casdoor SDK via Client ID & Client Secret, so the used Email provider will be the application' Email provider or the default Email provider
	// when receiver is the reserved keyword: "TestSmtpServer", it means to test the SMTP server instead of sending a real Email
	// "You have requested a verification code at Casdoor. Here is your code: %s, please enter in 5 minutes."
// SendSms
// @Title SendSms
// @Tag Service API
// @Description This API is not for Casdoor frontend to call, it is for Casdoor SDKs.
// @Param   clientId    query    string  true        "The clientId of the application"
// @Param   clientSecret    query    string  true    "The clientSecret of the application"
// @Param   from    body   controllers.SmsForm    true           "Details of the sms request"
// @Success 200 {object} controllers.Response The Response object
// @router /send-sms [post]
func (c *ApiController) SendSms() {
// SendNotification
// @Title SendNotification
// @Tag Service API
// @Description This API is not for Casdoor frontend to call, it is for Casdoor SDKs.
// @Param   from    body   controllers.NotificationForm    true         "Details of the notification request"
// @Success 200 {object} controllers.Response The Response object
// @router /send-notification [post]
func (c *ApiController) SendNotification() {