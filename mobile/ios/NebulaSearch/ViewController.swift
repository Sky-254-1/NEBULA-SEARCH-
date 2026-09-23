import UIKit
import WebKit
import LocalAuthentication

class ViewController: UIViewController, WKNavigationDelegate, WKScriptMessageHandler {

    private var webView: WKWebView!
    private let apiBaseUrl = "http://localhost:8000"

    override func viewDidLoad() {
        super.viewDidLoad()

        // Configure WebView
        let contentController = WKUserContentController()
        contentController.add(self, name: "NebulaBridge")

        let config = WKWebViewConfiguration()
        config.userContentController = contentController
        config.allowsInlineMediaPlayback = true

        webView = WKWebView(frame: view.bounds, configuration: config)
        webView.navigationDelegate = self
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(webView)

        // Load the frontend
        if let url = URL(string: "http://localhost:5173") {
            webView.load(URLRequest(url: url))
        }
    }

    // MARK: - WKNavigationDelegate

    func webView(
        _ webView: WKWebView,
        decidePolicyFor navigationAction: WKNavigationAction,
        decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
    ) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }

        if url.absoluteString.starts(with: apiBaseUrl) ||
           url.absoluteString.starts(with: "http://localhost:5173") {
            decisionHandler(.allow)
        } else if url.scheme == "http" || url.scheme == "https" {
            // Open external links in Safari
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
        } else {
            decisionHandler(.allow)
        }
    }

    // MARK: - WKScriptMessageHandler

    func userContentController(
        _ userContentController: WKUserContentController,
        didReceive message: WKScriptMessage
    ) {
        guard message.name == "NebulaBridge" else { return }

        if let body = message.body as? [String: Any],
           let action = body["action"] as? String {
            switch action {
            case "getApiBaseUrl":
                sendToWebView("apiBaseUrl", value: apiBaseUrl)
            case "authenticate":
                authenticateWithBiometrics()
            case "getPlatform":
                sendToWebView("platform", value: "ios")
            default:
                break
            }
        }
    }

    // MARK: - Biometric Auth

    private func authenticateWithBiometrics() {
        let context = LAContext()
        var error: NSError?

        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            sendToWebView("biometricError", value: "Biometric not available")
            return
        }

        context.evaluatePolicy(
            .deviceOwnerAuthenticationWithBiometrics,
            localizedReason: "Authenticate to continue"
        ) { [weak self] success, _ in
            DispatchQueue.main.async {
                if success {
                    self?.sendToWebView("biometricSuccess", value: "true")
                } else {
                    self?.sendToWebView("biometricError", value: "Authentication failed")
                }
            }
        }
    }

    // MARK: - Helpers

    private func sendToWebView(_ key: String, value: String) {
        let script = "window.dispatchEvent(new CustomEvent('\(key)', { detail: '\(value)' }));"
        webView.evaluateJavaScript(script, completionHandler: nil)
    }
}