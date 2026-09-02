package controllers
type ReleaseInfo struct {
// @Title getBinaryNames
// @Description Get binary names for different platforms and architectures
// @Success 200 {map[string]string} map[string]string "Binary names map"
func getBinaryNames() map[string]string {
// @Title getFinalBinaryName
// @Description Get final binary name for specific language
// @Param lang string true "Language type (go/java/rust)"
// @Success 200 {string} string "Final binary name"
func getFinalBinaryName(lang string) string {
// @Title getLatestCLIURL
// @Description Get latest CLI download URL from GitHub
// @Param repoURL string true "GitHub repository URL"
// @Param language string true "Language type"
// @Success 200 {string} string "Download URL and version"
func getLatestCLIURL(repoURL string, language string) (string, string, error) {
// @Title extractGoCliFile
// @Description Extract the Go CLI file
// @Param filePath string true "The file path"
// @Success 200 {string} string "The extracted file path"
// @router /extractGoCliFile [post]
func extractGoCliFile(filePath string) error {
// @Title unzipFile
// @Description Unzip the file
// @Param zipPath string true "The zip file path"
// @Param destDir string true "The destination directory"
// @Success 200 {string} string "The extracted file path"
// @router /unzipFile [post]
func unzipFile(zipPath, destDir string) error {
// @Title untarFile
// @Description Untar the file
// @Param tarPath string true "The tar file path"
// @Param destDir string true "The destination directory"
// @Success 200 {string} string "The extracted file path"
// @router /untarFile [post]
func untarFile(tarPath, destDir string) error {
// @Title createJavaCliWrapper
// @Description Create the Java CLI wrapper
// @Param binPath string true "The binary path"
// @Success 200 {string} string "The created file path"
// @router /createJavaCliWrapper [post]
func createJavaCliWrapper(binPath string) error {
		// Create a Windows CMD file
		// Create Unix shell script
// @Title downloadCLI
// @Description Download and setup CLI tools
// @Success 200 {error} error "Error if any"
func downloadCLI() error {
// @Title RefreshEngines
// @Tag CLI API
// @Description Refresh all CLI engines
// @Param m query string true "Hash for request validation"
// @Param t query string true "Timestamp for request validation"
// @Success 200 {object} controllers.Response The Response object
// @router /refresh-engines [post]
func (c *ApiController) RefreshEngines() {
// @Title ScheduleCLIUpdater
// @Description Start periodic CLI update scheduler
func ScheduleCLIUpdater() {
// @Title DownloadCLI
// @Description Download the CLI
// @Success 200 {string} string "The downloaded file path"
// @router /downloadCLI [post]
func DownloadCLI() error {
// @Title InitCLIDownloader
// @Description Initialize CLI downloader and start update scheduler
func InitCLIDownloader() {