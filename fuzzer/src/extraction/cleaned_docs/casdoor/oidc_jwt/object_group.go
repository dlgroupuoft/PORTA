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
type Group struct {
type GroupNode struct{}
func GetGroupCount(owner, field, value string) (int64, error) {
func GetGroups(owner string) ([]*Group, error) {
func GetGlobalGroups() ([]*Group, error) {
func GetPaginationGroups(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Group, error) {
func GetGroupsHaveChildrenMap(groups []*Group) (map[string]*Group, error) {
func getGroup(owner string, name string) (*Group, error) {
func GetGroup(id string) (*Group, error) {
func UpdateGroup(id string, group *Group) (bool, error) {
func AddGroup(group *Group) (bool, error) {
func AddGroups(groups []*Group) (bool, error) {
func AddGroupsInBatch(groups []*Group) (bool, error) {
func deleteGroup(group *Group) (bool, error) {
func DeleteGroup(group *Group) (bool, error) {
func checkGroupName(name string) error {
func (group *Group) GetId() string {
func ConvertToTreeData(groups []*Group, parentId string) []*Group {
func GetGroupUserCount(groupId string, field, value string) (int64, error) {
func GetPaginationGroupUsers(groupId string, offset, limit int, field, value, sortField, sortOrder string) ([]*User, error) {
func GetGroupUsers(groupId string) ([]*User, error) {
func GetGroupUsersWithoutError(groupId string) []*User {
func ExtendGroupWithUsers(group *Group) error {
func ExtendGroupsWithUsers(groups []*Group) error {
func GroupChangeTrigger(oldName, newName string) error {