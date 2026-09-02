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
type Session struct {
func GetSessions(owner string) ([]*Session, error) {
func GetUserSessions(owner string, name string) ([]*Session, error) {
func GetUserAppSessions(owner string, name string, application string) ([]*Session, error) {
func GetPaginationSessions(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Session, error) {
func GetSessionCount(owner, field, value string) (int64, error) {
func GetSingleSession(id string) (*Session, error) {
func UpdateSession(id string, session *Session) (bool, error) {
func removeExtraSessionIds(session *Session) {
func AddSession(session *Session) (bool, error) {
func DeleteSession(id, curSessionId string) (bool, error) {
		// If session doesn't exist, return success with no rows affected
		// This is a valid state (e.g., when a user has no active session)
func DeleteAllUserSessions(owner string, name string) (bool, error) {
func DeleteSessionId(id string, sessionId string) (bool, error) {
func DeleteBeegoSession(sessionIds []string) {
func (session *Session) GetId() string {
func IsSessionDuplicated(id string, sessionId string) (bool, error) {