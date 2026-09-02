// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
type Invitation struct {
func GetInvitationCount(owner, field, value string) (int64, error) {
func GetInvitations(owner string) ([]*Invitation, error) {
func GetPaginationInvitations(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Invitation, error) {
func getInvitation(owner string, name string) (*Invitation, error) {
func GetInvitation(id string) (*Invitation, error) {
func GetInvitationByCode(code string, organizationName string, lang string) (*Invitation, string) {
func GetMaskedInvitation(invitation *Invitation) *Invitation {
func UpdateInvitation(id string, invitation *Invitation, lang string) (bool, error) {
func AddInvitation(invitation *Invitation, lang string) (bool, error) {
func DeleteInvitation(invitation *Invitation) (bool, error) {
func (invitation *Invitation) GetId() string {
func VerifyInvitation(id string) (payment *Payment, attachInfo map[string]interface{}, err error) {
func (invitation *Invitation) SimpleCheckInvitationCode(invitationCode string, lang string) (bool, string) {
	// Determine whether the invitation code is in the form of a regular expression other than pure numbers and letters
func (invitation *Invitation) IsInvitationCodeValid(application *Application, invitationCode string, username string, email string, phone string, lang string) (bool, string) {
func (invitation *Invitation) GetInvitationLink(host string, application string) string {