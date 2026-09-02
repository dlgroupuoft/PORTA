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
func getSmsClient(provider *Provider) (sender.SmsClient, error) {
		// For Twilio, the message body is pre-formatted in SendSms using the template.
		// Pass "%s" as the template so go-sms-sender's fmt.Sprintf passes the content through unchanged.
func SendSms(provider *Provider, content string, phoneNumbers ...string) error {
		// Pre-format the message body using the provider's template.
		// If the template contains "%s", substitute the code; otherwise use the content (code) directly.