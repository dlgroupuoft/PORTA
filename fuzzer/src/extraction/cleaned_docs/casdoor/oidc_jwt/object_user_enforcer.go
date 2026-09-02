package object
type UserGroupEnforcer struct {
	// use rbac model implement use group, the enforcer can also implement user role
func NewUserGroupEnforcer(enforcer *casbin.Enforcer) *UserGroupEnforcer {
func (e *UserGroupEnforcer) checkModel() error {
func (e *UserGroupEnforcer) AddGroupForUser(user string, group string) (bool, error) {
func (e *UserGroupEnforcer) AddGroupsForUser(user string, groups []string) (bool, error) {
func (e *UserGroupEnforcer) DeleteGroupForUser(user string, group string) (bool, error) {
func (e *UserGroupEnforcer) DeleteGroupsForUser(user string) (bool, error) {
func (e *UserGroupEnforcer) GetGroupsForUser(user string) ([]string, error) {
func (e *UserGroupEnforcer) GetAllUsersByGroup(group string) ([]string, error) {
func GetGroupWithPrefix(group string) string {
func GetGroupWithoutPrefix(group string) string {
func (e *UserGroupEnforcer) GetUserNamesByGroupName(groupName string) ([]string, error) {
func (e *UserGroupEnforcer) UpdateGroupsForUser(user string, groups []string) (bool, error) {