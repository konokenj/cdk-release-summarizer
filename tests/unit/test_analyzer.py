import pytest
from src.github_release_summarizer.analyzer import PageAnalyzer, PullRequest
from unittest.mock import Mock, patch
import requests

import re


def test_get_pull_requests_from_release_covers_all_sections():
    """
    Test that get_pull_requests_from_release correctly handles all sections:
    features, bug fixes, alpha features, and alpha bug fixes.
    """
    analyzer = PageAnalyzer()

    mock_content = """
    <h3>Features</h3>
    <ul>
        <li>New feature 1 (#101)</li>
        <li>New feature 2 (#102)</li>
    </ul>
    <h3>Bug Fixes</h3>
    <ul>
        <li>Fixed bug 1 (#201)</li>
    </ul>
    <h2>Alpha modules</h2>
    <h3>Features</h3>
    <ul>
        <li>Alpha feature 1 (#301)</li>
    </ul>
    <h3>Bug Fixes</h3>
    <ul>
        <li>Alpha bug fix 1 (#401)</li>
    </ul>
    """

    with patch("requests.get") as mock_get:
        mock_get.return_value.text = mock_content

        result = analyzer.get_pull_requests_from_release("https://example.com")

    expected_pull_requests = [
        PullRequest(category="feature", title="New feature 1", pr_number="101"),
        PullRequest(category="feature", title="New feature 2", pr_number="102"),
        PullRequest(category="bug fix", title="Fixed bug 1", pr_number="201"),
        PullRequest(category="alpha feature", title="Alpha feature 1", pr_number="301"),
        PullRequest(category="alpha bug fix", title="Alpha bug fix 1", pr_number="401"),
    ]

    assert result == expected_pull_requests


@patch("requests.get")
def test_get_pull_requests_from_release_empty_content(mock_get):
    """
    Test get_pull_requests_from_release with empty content
    """
    mock_response = Mock()
    mock_response.text = ""
    mock_get.return_value = mock_response

    analyzer = PageAnalyzer()
    result = analyzer.get_pull_requests_from_release("http://example.com")
    assert result == []


def test_get_pull_requests_from_release_empty_url():
    """
    Test get_pull_requests_from_release with an empty URL
    """
    analyzer = PageAnalyzer()
    with pytest.raises(ValueError):
        analyzer.get_pull_requests_from_release("")


@patch("requests.get")
def test_get_pull_requests_from_release_invalid_html(mock_get):
    """
    Test get_pull_requests_from_release with invalid HTML content
    """
    mock_response = Mock()
    mock_response.text = "<invalid>HTML</content>"
    mock_get.return_value = mock_response

    analyzer = PageAnalyzer()
    result = analyzer.get_pull_requests_from_release("http://example.com")
    assert result == []


def test_get_pull_requests_from_release_invalid_url():
    """
    Test get_pull_requests_from_release with an invalid URL
    """
    analyzer = PageAnalyzer()
    with pytest.raises(requests.exceptions.RequestException):
        analyzer.get_pull_requests_from_release("http://invalid.url")


@patch("requests.get")
def test_get_pull_requests_from_release_missing_sections(mock_get):
    """
    Test get_pull_requests_from_release with missing sections
    """
    mock_response = Mock()
    mock_response.text = (
        "<html><body><h1>Release Notes</h1><p>No sections here</p></body></html>"
    )
    mock_get.return_value = mock_response

    analyzer = PageAnalyzer()
    result = analyzer.get_pull_requests_from_release("http://example.com")
    assert result == []


@patch("requests.get")
def test_get_pull_requests_from_release_network_error(mock_get):
    """
    Test get_pull_requests_from_release with a network error
    """
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    analyzer = PageAnalyzer()
    with pytest.raises(requests.exceptions.RequestException):
        analyzer.get_pull_requests_from_release("http://example.com")


def test_get_pull_requests_from_release_no_features_with_alpha():
    """
    Test get_pull_requests_from_release when there are no regular features,
    but there are bug fixes, alpha features, and alpha bug fixes.
    """
    mock_content = """
    <h3>Bug Fixes</h3>
    <ul>
        <li>Fix a bug (#123)</li>
    </ul>
    <h2>Alpha modules</h2>
    <h3>Features</h3>
    <ul>
        <li>New alpha feature (#456)</li>
    </ul>
    <h3>Bug Fixes</h3>
    <ul>
        <li>Fix alpha bug (#789)</li>
    </ul>
    """

    with patch("requests.get") as mock_get:
        mock_get.return_value.text = mock_content

        analyzer = PageAnalyzer()
        result = analyzer.get_pull_requests_from_release("https://example.com")

        expected = [
            PullRequest(category="bug fix", title="Fix a bug", pr_number="123"),
            PullRequest(
                category="alpha feature", title="New alpha feature", pr_number="456"
            ),
            PullRequest(
                category="alpha bug fix", title="Fix alpha bug", pr_number="789"
            ),
        ]

        assert result == expected


@patch("requests.get")
def test_get_pull_requests_from_release_no_pull_requests(mock_get):
    """
    Test get_pull_requests_from_release with content that has no pull requests
    """
    mock_response = Mock()
    mock_response.text = "<html><body><h1>Release Notes</h1></body></html>"
    mock_get.return_value = mock_response

    analyzer = PageAnalyzer()
    result = analyzer.get_pull_requests_from_release("http://example.com")
    assert result == []


def test_get_pull_requests_from_release_with_l1_and_alpha_modules():
    """
    Test get_pull_requests_from_release with L1 CloudFormation update, features, and alpha modules
    """
    analyzer = PageAnalyzer()

    mock_html = """
    <h3>Features</h3>
    <ul>
        <li>update L1 CloudFormation resource definitions (#1234)</li>
        <li>New feature (#5678)</li>
    </ul>
    <h2>Alpha modules</h2>
    <h3>Features</h3>
    <ul>
        <li>Alpha feature (#9101)</li>
    </ul>
    <h3>Bug Fixes</h3>
    <ul>
        <li>Alpha bug fix (#1121)</li>
    </ul>
    """

    with patch("requests.get") as mock_get:
        mock_get.return_value.text = mock_html

        result = analyzer.get_pull_requests_from_release("http://example.com")

    expected_result = [
        PullRequest(category="feature", title="New feature", pr_number="5678"),
        PullRequest(
            category="L1",
            title="update L1 CloudFormation resource definitions",
            pr_number="1234",
        ),
        PullRequest(category="alpha feature", title="Alpha feature", pr_number="9101"),
        PullRequest(category="alpha bug fix", title="Alpha bug fix", pr_number="1121"),
    ]

    assert result == expected_result


def test_get_pull_requests_with_all_sections():
    """
    Test get_pull_requests_from_release with all sections present
    """
    # Mock the requests.get call
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = """
        <h3>Features</h3>
        <ul>
            <li>update L1 CloudFormation resource definitions (#1234)</li>
            <li>Add new feature (#5678)</li>
        </ul>
        <h3>Bug Fixes</h3>
        <ul>
            <li>Fix critical bug (#9012)</li>
        </ul>
        <h2>Alpha modules</h2>
        <h3>Features</h3>
        <ul>
            <li>New alpha feature (#3456)</li>
        </ul>
        <h3>Bug Fixes</h3>
        <ul>
            <li>Fix alpha bug (#7890)</li>
        </ul>
        """
        mock_get.return_value = mock_response

        analyzer = PageAnalyzer()
        result = analyzer.get_pull_requests_from_release("https://example.com/release")

        expected_result = [
            PullRequest(category="feature", title="Add new feature", pr_number="5678"),
            PullRequest(
                category="L1",
                title="update L1 CloudFormation resource definitions",
                pr_number="1234",
            ),
            PullRequest(category="bug fix", title="Fix critical bug", pr_number="9012"),
            PullRequest(
                category="alpha feature", title="New alpha feature", pr_number="3456"
            ),
            PullRequest(
                category="alpha bug fix", title="Fix alpha bug", pr_number="7890"
            ),
        ]

        assert result == expected_result
        mock_get.assert_called_once_with("https://example.com/release")


def test_get_pull_requests_with_all_sections_2():
    """
    Test get_pull_requests_from_release with all sections present
    """
    # Mock the requests.get method
    with patch("requests.get") as mock_get:
        # Create a mock response
        mock_response = Mock()
        mock_response.text = """
        <h3>Features</h3>
        <ul>
            <li>update L1 CloudFormation resource definitions (#1234)</li>
            <li>Add new feature (#5678)</li>
        </ul>
        <h3>Bug Fixes</h3>
        <ul>
            <li>Fix critical bug (#9012)</li>
        </ul>
        <h2>Alpha modules</h2>
        <h3>Features</h3>
        <ul>
            <li>New alpha feature (#3456)</li>
        </ul>
        <h3>Bug Fixes</h3>
        <ul>
            <li>Fix alpha bug (#7890)</li>
        </ul>
        """
        mock_get.return_value = mock_response

        # Create an instance of PageAnalyzer
        analyzer = PageAnalyzer()

        # Call the method under test
        result = analyzer.get_pull_requests_from_release("http://example.com")

        # Assert the results
        expected_result = [
            PullRequest(category="feature", title="Add new feature", pr_number="5678"),
            PullRequest(
                category="L1",
                title="update L1 CloudFormation resource definitions",
                pr_number="1234",
            ),
            PullRequest(category="bug fix", title="Fix critical bug", pr_number="9012"),
            PullRequest(
                category="alpha feature", title="New alpha feature", pr_number="3456"
            ),
            PullRequest(
                category="alpha bug fix", title="Fix alpha bug", pr_number="7890"
            ),
        ]

        assert result == expected_result

        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with("http://example.com")


def test_get_pull_requests_with_l1_feature_and_bug_fix():
    """
    Test get_pull_requests_from_release with L1 feature, regular feature, and bug fix
    """
    # Mock the requests.get() call
    mock_response = Mock()
    mock_response.text = """
    <h3>Features</h3>
    <ul>
        <li>update L1 CloudFormation resource definitions (#1234)</li>
        <li>Add new feature (#5678)</li>
    </ul>
    <h3>Bug Fixes</h3>
    <ul>
        <li>Fix critical bug (#9012)</li>
    </ul>
    """

    with patch("requests.get", return_value=mock_response):
        analyzer = PageAnalyzer()
        result = analyzer.get_pull_requests_from_release("https://example.com/release")

    expected_result = [
        PullRequest(category="feature", title="Add new feature", pr_number="5678"),
        PullRequest(
            category="L1",
            title="update L1 CloudFormation resource definitions",
            pr_number="1234",
        ),
        PullRequest(category="bug fix", title="Fix critical bug", pr_number="9012"),
    ]

    assert result == expected_result


def test_get_l1_update_edge_case_duplicate_resources():
    """
    Test get_l1_update with duplicate resources
    """
    analyzer = PageAnalyzer()
    content = "[+] resource Resource1 [+] resource Resource1 [+] service Service1"
    result = analyzer.get_l1_update(content)
    assert result == ["Resource1", "Resource1", "Service1"]


def test_get_l1_update_edge_case_multiple_resources():
    """
    Test get_l1_update with multiple resources
    """
    analyzer = PageAnalyzer()
    content = "[+] resource Resource1 [+] resource Resource2 [+] service Service1"
    result = analyzer.get_l1_update(content)
    assert result == ["Resource1", "Resource2", "Service1"]


def test_get_l1_update_edge_case_whitespace():
    """
    Test get_l1_update with extra whitespace
    """
    analyzer = PageAnalyzer()
    content = "[+] resource   Resource1   [+] service   Service1  "
    result = analyzer.get_l1_update(content)
    assert result == ["Resource1", "Service1"]


def test_get_l1_update_empty_input():
    """
    Test get_l1_update with empty input
    """
    analyzer = PageAnalyzer()
    result = analyzer.get_l1_update("")
    assert result == []


def test_get_l1_update_exception_handling():
    """
    Test get_l1_update exception handling
    """
    analyzer = PageAnalyzer()
    with patch("re.findall", side_effect=Exception("Mocked exception")):
        with pytest.raises(Exception):
            analyzer.get_l1_update("Some content")


def test_get_l1_update_incorrect_format():
    """
    Test get_l1_update with incorrect format
    """
    analyzer = PageAnalyzer()
    result = analyzer.get_l1_update("[+] resourceInvalidFormat")
    assert result == []


def test_get_l1_update_invalid_input():
    """
    Test get_l1_update with invalid input
    """
    analyzer = PageAnalyzer()
    result = analyzer.get_l1_update(
        "This is some text without any resources or services"
    )
    assert result == []


def test_get_l1_update_with_resources_and_services():
    """
    Test get_l1_update method with content containing both resources and services
    """
    analyzer = PageAnalyzer()
    content = """
    [+] resource AWS::EC2::Instance
    [+] service AWS::Lambda
    """
    result = analyzer.get_l1_update(content)
    assert result == ["AWS::EC2::Instance", "AWS::Lambda"]


def test_get_related_issues_case_insensitive():
    """
    Test get_related_issues case insensitivity
    """
    analyzer = PageAnalyzer()
    content = "This CLOSES #123 and Fixes #456."
    result = analyzer.get_related_issues(content)
    assert set(result) == set(["123", "456"])


def test_get_related_issues_empty_input():
    """
    Test get_related_issues with empty input
    """
    analyzer = PageAnalyzer()
    result = analyzer.get_related_issues("")
    assert result == []


def test_get_related_issues_exception_handling():
    """
    Test get_related_issues exception handling
    """
    analyzer = PageAnalyzer()
    with patch("re.findall", side_effect=Exception("Mocked exception")):
        with pytest.raises(Exception):
            analyzer.get_related_issues("Some content")


def test_get_related_issues_large_input():
    """
    Test get_related_issues with a large input
    """
    analyzer = PageAnalyzer()
    large_content = " ".join([f"fixes #{i}" for i in range(1000)])
    result = analyzer.get_related_issues(large_content)
    assert len(result) == 1000
    assert set(result) == set(map(str, range(1000)))


def test_get_related_issues_multiple_matches():
    """
    Test get_related_issues with multiple matches in different formats
    """
    analyzer = PageAnalyzer()
    content = "This closes #123, fixes #456 and resolves #789. Also FIXED #101."
    result = analyzer.get_related_issues(content)
    assert set(result) == set(["123", "456", "789", "101"])


def test_get_related_issues_no_matches():
    """
    Test get_related_issues with input that doesn't contain any matches
    """
    analyzer = PageAnalyzer()
    content = "This is a test content without any issue references."
    result = analyzer.get_related_issues(content)
    assert result == []


def test_get_related_issues_with_non_ascii_characters():
    """
    Test get_related_issues with non-ASCII characters
    """
    analyzer = PageAnalyzer()
    content = "This closes #123 and fixes #456. また、これは問題 #789 を解決します。"
    result = analyzer.get_related_issues(content)
    assert set(result) == set(["123", "456"])


def test_get_related_issues_with_surrounding_text():
    """
    Test get_related_issues with issue references surrounded by text
    """
    analyzer = PageAnalyzer()
    content = "This is a fix for closed #123 and resolves #456 in the codebase."
    result = analyzer.get_related_issues(content)
    assert set(result) == set(["123", "456"])


def test_filter_comments_by_user_empty_body():
    """
    Test filter_comments_by_user with empty body in User comment
    """
    analyzer = PageAnalyzer()
    comments_data = [
        {"user": {"type": "User"}, "body": ""},
        {"user": {"type": "User"}, "body": "Non-empty comment"},
    ]
    result = analyzer.filter_comments_by_user(comments_data)
    assert result == ["", "Non-empty comment"]


def test_filter_comments_by_user_empty_input():
    """
    Test filter_comments_by_user with an empty input list
    """
    analyzer = PageAnalyzer()
    result = analyzer.filter_comments_by_user([])
    assert result == []


def test_filter_comments_by_user_incorrect_format():
    """
    Test filter_comments_by_user with incorrect input format
    """
    analyzer = PageAnalyzer()
    incorrect_format = [{"user": "not a dict", "body": "comment"}]
    with pytest.raises(TypeError):
        analyzer.filter_comments_by_user(incorrect_format)


def test_filter_comments_by_user_invalid_input():
    """
    Test filter_comments_by_user with invalid input (missing required keys)
    """
    analyzer = PageAnalyzer()
    invalid_input = [{"invalid": "data"}]
    with pytest.raises(KeyError):
        analyzer.filter_comments_by_user(invalid_input)


def test_filter_comments_by_user_large_input():
    """
    Test filter_comments_by_user with a large input
    """
    analyzer = PageAnalyzer()
    large_input = [
        {"user": {"type": "User"}, "body": f"Comment {i}"} for i in range(10000)
    ]
    result = analyzer.filter_comments_by_user(large_input)
    assert len(result) == 10000
    assert all(comment.startswith("Comment ") for comment in result)


def test_filter_comments_by_user_missing_body():
    """
    Test filter_comments_by_user with missing 'body' key in comment
    """
    analyzer = PageAnalyzer()
    comments_data = [{"user": {"type": "User"}}]
    with pytest.raises(KeyError):
        analyzer.filter_comments_by_user(comments_data)


def test_filter_comments_by_user_non_user_type():
    """
    Test filter_comments_by_user with non-User type comments
    """
    analyzer = PageAnalyzer()
    comments_data = [
        {"user": {"type": "Bot"}, "body": "Bot comment"},
        {"user": {"type": "User"}, "body": "User comment"},
        {"user": {"type": "Organization"}, "body": "Org comment"},
    ]
    result = analyzer.filter_comments_by_user(comments_data)
    assert result == ["User comment"]


def test_filter_comments_by_user_unicode_characters():
    """
    Test filter_comments_by_user with Unicode characters in comments
    """
    analyzer = PageAnalyzer()
    comments_data = [
        {"user": {"type": "User"}, "body": "Comment with Unicode: 你好"},
        {"user": {"type": "User"}, "body": "Another Unicode comment: こんにちは"},
    ]
    result = analyzer.filter_comments_by_user(comments_data)
    assert result == [
        "Comment with Unicode: 你好",
        "Another Unicode comment: こんにちは",
    ]


should_excluded = """\
diff --git a/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/aws-cdk-elbv2-integ.assets.json b/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/aws-cdk-elbv2-integ.assets.json
index 392c1e5a4472f..b10a58ad1024a 100644
--- a/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/aws-cdk-elbv2-integ.assets.json
+++ b/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/aws-cdk-elbv2-integ.assets.json
@@ -1,7 +1,7 @@
 {
-  "version": "20.0.0",
+  "version": "36.0.0",
   "files": {
-    "20103c6961e413b3b62b7b83afb397628bcd5f1b600fe84a871503e214a8bc02": {
+    "0109ed980d060e788d5ff84f66ab8a5a33ceee66748b8a6d04946fe7a20aa670": {
       "source": {
         "path": "aws-cdk-elbv2-integ.template.json",
         "packaging": "file"
@@ -9,7 +9,7 @@
       "destinations": {
         "current_account-current_region": {
           "bucketName": "cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}",
-          "objectKey": "20103c6961e413b3b62b7b83afb397628bcd5f1b600fe84a871503e214a8bc02.json",
+          "objectKey": "0109ed980d060e788d5ff84f66ab8a5a33ceee66748b8a6d04946fe7a20aa670.json",
           "assumeRoleArn": "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/cdk-hnb659fds-file-publishing-role-${AWS::AccountId}-${AWS::Region}"
         }
       }
diff --git a/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/cdk.out b/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/cdk.out
index 588d7b269d34f..1f0068d32659a 100644
--- a/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/cdk.out
+++ b/packages/@aws-cdk-testing/framework-integ/test/aws-route53-targets/test/integ.alb-alias-target.js.snapshot/cdk.out
@@ -1 +1 @@
-{"version":"20.0.0"}
\\ No newline at end of file
+{"version":"36.0.0"}
\\ No newline at end of file
"""

should_included = """\
diff --git a/packages/aws-cdk-lib/aws-route53/lib/alias-record-target.ts b/packages/aws-cdk-lib/aws-route53/lib/alias-record-target.ts
index e9c2248f0b470..afb3537b40cea 100644
--- a/packages/aws-cdk-lib/aws-route53/lib/alias-record-target.ts
+++ b/packages/aws-cdk-lib/aws-route53/lib/alias-record-target.ts
@@ -25,4 +25,11 @@ export interface AliasRecordTargetConfig {
    * DNS name of the target
    */
   readonly dnsName: string;
+
+  /**
+   * Evaluate the target health
+   *
+   * @default - no health check configuration
+   */
+  readonly evaluateTargetHealth?: boolean;
 }
diff --git a/packages/aws-cdk-lib/aws-route53/test/record-set.test.ts b/packages/aws-cdk-lib/aws-route53/test/record-set.test.ts
index 812236eb18e18..a16e5ac4cf91e 100644
--- a/packages/aws-cdk-lib/aws-route53/test/record-set.test.ts
+++ b/packages/aws-cdk-lib/aws-route53/test/record-set.test.ts
@@ -188,6 +188,46 @@ describe('record set', () => {
     });
   });

+  test('A record with alias health check', () => {
+    // GIVEN
+    const stack = new Stack();
+
+    const zone = new route53.HostedZone(stack, 'HostedZone', {
+      zoneName: 'myzone',
+    });
+
+    const target: route53.IAliasRecordTarget = {
+      bind: () => {
+        return {
+          hostedZoneId: 'Z2P70J7EXAMPLE',
+          dnsName: 'foo.example.com',
+          evaluateTargetHealth: true,
+        };
+      },
+    };
+
+    // WHEN
+    new route53.ARecord(zone, 'Alias', {
+      zone,
+      recordName: '_foo',
+      target: route53.RecordTarget.fromAlias(target),
+    });
+
+    // THEN
+    Template.fromStack(stack).hasResourceProperties('AWS::Route53::RecordSet', {
+      Name: '_foo.myzone.',
+      HostedZoneId: {
+        Ref: 'HostedZoneDB99F866',
+      },
+      Type: 'A',
+      AliasTarget: {
+        HostedZoneId: 'Z2P70J7EXAMPLE',
+        DNSName: 'foo.example.com',
+        EvaluateTargetHealth: true,
+      },
+    });
+  });
+
   test('A record with health check', () => {
     // GIVEN
     const stack = new Stack();
@@ -1501,4 +1541,3 @@ describe('record set', () => {
     })).toThrow('multiValueAnswer cannot be specified for alias record');
   });
 });
-
"""


def test_filter_diff_all_excluded():
    """
    Test filter_diff when all chunks are excluded
    """
    analyzer = PageAnalyzer()
    input_content = should_excluded
    result = analyzer.filter_diff(input_content)
    assert result == ""


def test_filter_diff_custom_exclude_pattern():
    """
    Test filter_diff with a custom exclude pattern
    """
    analyzer = PageAnalyzer()
    input_content = """\
diff --git a/file1.txt b/file1.txt
diff --git a/file2.exclude b/file2.exclude
"""
    result = analyzer.filter_diff(input_content, exclude_pattern=r"\.exclude")
    assert "file1.txt" in result
    assert "file2.exclude" not in result


def test_filter_diff_empty_input():
    """
    Test filter_diff with empty input
    """
    analyzer = PageAnalyzer()
    result = analyzer.filter_diff("")
    assert result == ""


def test_filter_diff_exception_handling():
    """
    Test filter_diff exception handling
    """
    analyzer = PageAnalyzer()
    with pytest.raises(Exception):
        with patch("re.search", side_effect=Exception("Mocked exception")):
            analyzer.filter_diff("diff --git a/file1 b/file1\n")


def test_filter_diff_exclude_pattern():
    """
    Test filter_diff method with exclude pattern matching
    """
    analyzer = PageAnalyzer()
    content = should_excluded + should_included
    result = analyzer.filter_diff(content)
    assert result == should_included


def test_filter_diff_invalid_regex_pattern():
    """
    Test filter_diff with an invalid regex pattern
    """
    analyzer = PageAnalyzer()
    with pytest.raises(re.error):
        analyzer.filter_diff("diff --git a/file1 b/file1\n", exclude_pattern="[")


def test_filter_diff_no_diff_git_header():
    """
    Test filter_diff with input that doesn't contain 'diff --git'
    """
    analyzer = PageAnalyzer()
    input_content = "Some content without diff --git header"
    result = analyzer.filter_diff(input_content)
    assert result == input_content


def test_filter_diff_unicode_characters():
    """
    Test filter_diff with Unicode characters
    """
    analyzer = PageAnalyzer()
    input_content = """\
diff --git a/file_unicode.txt b/file_unicode.txt
+こんにちは
-你好
"""
    result = analyzer.filter_diff(input_content)
    assert "こんにちは" in result
    assert "你好" in result
