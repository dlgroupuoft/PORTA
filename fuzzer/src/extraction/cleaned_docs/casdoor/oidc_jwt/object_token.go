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
type Token struct {
func GetTokenCount(owner, organization, field, value string) (int64, error) {
func GetTokens(owner string, organization string) ([]*Token, error) {
func GetPaginationTokens(owner, organization string, offset, limit int, field, value, sortField, sortOrder string) ([]*Token, error) {
func getToken(owner string, name string) (*Token, error) {
func getTokenByCode(code string) (*Token, error) {
func GetTokenByAccessToken(accessToken string) (*Token, error) {
func GetTokenByRefreshToken(refreshToken string) (*Token, error) {
func GetTokenByTokenValue(tokenValue, tokenTypeHint string) (*Token, error) {
func updateUsedByCode(token *Token) (bool, error) {
func GetToken(id string) (*Token, error) {
func (token *Token) GetId() string {
func getTokenHash(input string) string {
func (token *Token) popularHashes() {
func UpdateToken(id string, token *Token, isGlobalAdmin bool) (bool, error) {
func AddToken(token *Token) (bool, error) {
func DeleteToken(token *Token) (bool, error) {
func ExpireTokenByUser(owner, username string) (bool, error) {