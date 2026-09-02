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
type VerifyResult struct {
type verifyCodeErrorInfo struct {
func init() {
type VerificationRecord struct {
func IsAllowSend(user *User, remoteAddr, recordType string, application *Application) error {
	// Get timeout from application, or use default
func SendVerificationCodeToEmail(organization *Organization, user *User, provider *Provider, remoteAddr string, dest string, method string, host string, applicationName string, application *Application) error {
	// if organization.MasterVerificationCode != "" {
	//	code = organization.MasterVerificationCode
	// }
	// "You have requested a verification code at Casdoor. Here is your code: %s, please enter in 5 minutes."
func SendVerificationCodeToPhone(organization *Organization, user *User, provider *Provider, remoteAddr string, dest string, application *Application) error {
	// if organization.MasterVerificationCode != "" {
	//	code = organization.MasterVerificationCode
	// }
func AddToVerificationRecord(user *User, provider *Provider, organization *Organization, remoteAddr, recordType, dest, code string) error {
func filterRecordIn24Hours(record *VerificationRecord) *VerificationRecord {
func getVerificationRecord(dest string) (*VerificationRecord, error) {
func getUnusedVerificationRecord(dest string) (*VerificationRecord, error) {
func CheckVerificationCode(dest string, code string, lang string) (*VerifyResult, error) {
func DisableVerificationCode(dest string) error {
func CheckSigninCode(user *User, dest, code, lang string) error {
	// check the login error times
// getVerifyCodeErrorKey builds the in-memory key for verify-code failed attempt tracking
func getVerifyCodeErrorKey(user *User, dest string) string {
func checkVerifyCodeErrorTimes(user *User, dest, lang string) error {
func recordVerifyCodeErrorInfo(user *User, dest, lang string) error {
func resetVerifyCodeErrorTimes(user *User, dest string) {
func CheckVerifyCodeWithLimit(user *User, dest, code, lang string) error {
func CheckFaceId(user *User, faceId []float64, lang string) error {
func GetVerifyType(username string) (verificationCodeType string) {
// From Casnode/object/validateCode.go line 116
func getRandomCode(length int) string {
func GetVerificationCount(owner, field, value string) (int64, error) {
func GetVerifications(owner string) ([]*VerificationRecord, error) {
func GetUserVerifications(owner, user string) ([]*VerificationRecord, error) {
func GetPaginationVerifications(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*VerificationRecord, error) {
func getVerification(owner string, name string) (*VerificationRecord, error) {
func GetVerification(id string) (*VerificationRecord, error) {