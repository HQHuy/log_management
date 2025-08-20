import re
import json
from .clean_message import clean_log_message

class LogLabeler:
    def __init__(self, patterns=None):
        if patterns is None:
            patterns = {
                # HTTP Request Detail - Cải tiến để handle JSON data phức tạp hơn
                'HTTP_REQUEST_DETAIL': re.compile(
                    r'HTTP Request at (\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?) (success|fail) with detail:\s*(\{.*\})',
                    re.DOTALL
                ),
                
                # HTTP Request End - Đã sửa để capture đúng các groups
                'HTTP_REQUEST_END': re.compile(
                    r'Request finished "([^"]+)" "(\w+)" (.+?) - (\d+) (.+?) (?:"([^"]*)"|(\S+)) ([\d.]+)ms'
                ),

                # HTTP Request Start - Cải tiến để handle URL với query parameters
                'HTTP_REQUEST_START': re.compile(
                    r'Request starting "(?P<http_version>[^"]+)" "(?P<method>[^"]+)" (?P<raw_url>[^"]+)"?(?P<query_params>[^"]*)"? -'
                ),
                
                # HTTP Request Start Processing - Cải tiến
                'HTTP_REQUEST_START_PROCESSING': re.compile(
                    r'Start processing HTTP request "(?P<method>[^"]+)" "(?P<raw_url>[^"]+)"?(?P<query_params>[^"]*)"?'
                ),
                
                # HTTP Request Sending - Cải tiến
                'HTTP_REQUEST_SENDING': re.compile(
                    r'Sending HTTP request "(?P<method>[^"]+)" "(?P<raw_url>[^"]+)"?(?P<query_params>[^"]*)"?'
                ),
                
                # HTTP Response Received - Cải tiến để capture headers info
                'HTTP_RESPONSE_RECEIVED': re.compile(
                    r'Received HTTP response headers after ([\d.]+)ms - (\d+)(?: (.*))?'
                ),
                
                # HTTP Request End Processing - Cải tiến
                'HTTP_REQUEST_END_PROCESSING': re.compile(
                    r'End processing HTTP request after ([\d.]+)ms - (\d+)(?: (.*))?'
                ),
                
                # Database Query - Cải tiến để handle command details tốt hơn
                'DATABASE_QUERY': re.compile(
                    # r'Executed DbCommand \("([\d,.]+)"ms\)\s*(.*?)(?=\n|$)',
                    # re.DOTALL
                    r'Executed DbCommand\s*\("([\d,.]+)"ms\).*?(SELECT|INSERT|UPDATE|DELETE)\s+.*',
                    re.IGNORECASE | re.DOTALL
                ),
                
                # Performance Warning - Cải tiến để capture thêm context
                'PERFORMANCE_WARNING': re.compile(
                    r'WebAPI Long Running Request:\s*([^(]*?)\s*\((\d+) milliseconds\)'
                ),
                
                # API Request - Cải tiến để capture LogAction details
                'API_REQUEST': re.compile(
                    r'WebAPI Request:\s*(.*?)\s*LogAction\s*\{([^}]*)\}'
                ),
                
                # HTTP Status Set - Cải tiến để capture context
                'HTTP_STATUS_SET': re.compile(
                    r'Setting HTTP status code (\d+)(?:\s+(.*))?'
                ),
                
                # HTTP Write JSON - Cải tiến để capture type và context
                'HTTP_WRITE_JSON': re.compile(
                    r'Writing value of type\s*[\'"]{0,2}([\w.`\[\]+]+)[\'"]{0,2}\s*as Json(?:\s+(.*))?'
                ),
                
                # Redirect - Cải tiến để capture redirect context
                'REDIRECT': re.compile(
                    r'Executing RedirectResult, redirecting to "([^"]+)"(?:\s+(.*))?'
                ),
                
                # Static File - Cải tiến để handle các quote variations
                'STATIC_FILE': re.compile(
                    r'Sending file\.\s*Request path:\s*[\'"]+"?([^\'"\s]+)"?[\'"]?\.\s*Physical path:\s*[\'"]+"?([^\'"\s]+)"?[\'"]?'
                ),
                
                # File Download - Cải tiến
                'FILE_DOWNLOAD': re.compile(
                    r'Sending file with download name\s*[\'"]?([^\'"\s]+)[\'"]?\.'
                ),
                
                # Mongo Query - Cải tiến để handle pipeline tốt hơn
                'MONGO_QUERY': re.compile(
                    r'Executed MQL query\s*[\'\"]{1,3}([^.]+?\.[^.]+?)[\'\"]{1,3}\.aggregate\(\[(.*?)\]\)',
                    re.DOTALL
                ),
                
                # Bulk Write Operations - Cải tiến
                'BULK_WRITE_UNIVERSAL': re.compile(
                    r'(Executing|Executed) Bulk Write \("([\d,.]+)"\s*ms\)\s*Collection=\s*[\'"]+"?([^\'",]+)"?[\'"]?,\s*(?:Insertions=(\d+),\s*Deletions=(\d+),\s*Modifications=(\d+)|Inserted=(\d+),\s*Deleted=(\d+),\s*Modified=(\d+))'
                ),
                
                # Authorization Failed - Cải tiến
                'AUTHZ_FAILED': re.compile(
                    r'Authorization failed\.\s*[\'"]?([^\'"\n]*(?:requirements?|requirement)[^\'"\n]*)[\'"]?(?:\s+(.*))?',
                    re.IGNORECASE
                ),
                
                # Authentication Scheme - Cải tiến
                'AUTH_SCHEME_CHALLENGED': re.compile(
                    r'AuthenticationScheme:\s*[\'"]([^\'"\s]+)[\'\"]\s+(was challenged|was forbidden)(?:\s+(.*))?'
                ),
                
                # Challenge Result - Cải tiến để parse schemes tốt hơn
                'CHALLENGE_RESULT': re.compile(
                    r'Executing ChallengeResult with authentication schemes\s*\(([^)]*)\)\.(?:\s+(.*))?'
                ),
                
                # Transaction Begin - Cải tiến
                'TRANSACTION_BEGIN': re.compile(
                    r'Beginning transaction with options\s*[\'"]MaxCommitTime\s*[\'"]([^\'\"]*)[\'"],\s*ReadConcern\s*[\'"]([^\'\"]*)[\'"],\s*ReadPreference\s*[\'"]([^\'\"]*)[\'"],\s*WriteConcern\s*[\'"]([^\'\"]*)[\'"][\'"]'
                ),
                
                # Key Created - Cải tiến
                'KEY_CREATED': re.compile(
                    r'Creating key\s*\{([a-f0-9\-]+)\}\s*with creation date\s*([\d\-:\sZ]+),\s*activation date\s*([\d\-:\sZ]+),\s*and expiration date\s*([\d\-:\sZ]+)'
                ),
                
                # Invalid Cast - Cải tiến
                'INVALID_CAST': re.compile(
                    r'Invalid cast from\s*[\'"]([^\'\"]+)[\'\"]\s*to\s*[\'"]([^\'\"]+)[\'\"]\.'
                ),
                
                # Middleware Pipeline Not Handled - Đã sửa để match chính xác
                'MIDDLEWARE_PIPELINE_NOT_HANDLED': re.compile(
                    r'Request reached the end of the middleware pipeline without being handled by application code\.\s*Request path:\s*[\'"]([^\'\"]+)[\'\"]\s+([^,\s]+),?\s*Response status code:\s*(\d+)',
                    re.DOTALL
                ),
                
                # Index Error - Cải tiến
                'INDEX_ERROR': re.compile(
                    r'Index\s+[\'"]([^\'\"]+)[\'\"]\s+errors\.',
                    re.IGNORECASE
                ),
                
                # Search Document Failed - Cải tiến
                'SEARCH_DOCUMENT_FAILED': re.compile(
                    r'Failed to Search documents?\s+at index\s+[\'"]([^\'\"]+)[\'\"]\s*(?:\(from:(\d+),\s*size:(\d+)\))?\s*:\s*[\'"]([^\'\"]+)[\'"]',
                    re.IGNORECASE
                ),
                
                # File Not Modified - Cải tiến
                'FILE_NOT_MODIFIED': re.compile(
                    r'The file\s+[\'"]([^\'\"]+)[\'\"]\s+was not modified'
                ),
                
                # Dossier Count Fail - Cải tiến
                'DOSSIER_COUNT_FAIL': re.compile(
                    r'Fail to count dossier by filter\s+[\'"]([^\'\"]+)[\'\"]\s+with error\s+[\'"]([^\'\"]+)[\'"]'
                ),
                
                # System Info patterns - Giữ nguyên
                'SYSTEM_INFO': re.compile(
                    r'User profile is available|Acquiring an exclusive lock|Hosting environment|Content root path|CORS policy execution successful'
                ),
                
                'APP_STARTUP': re.compile(
                    r'Application started|No migrations were applied'
                ),
                
                'APP_SHUTDOWN': re.compile(
                    r'Application is shutting down\.\.\.'
                ),
                
                'ENDPOINT_EXEC': re.compile(
                    r'Executing endpoint|Executed endpoint'
                ),
                
                'INMEMORY_REPO_USED': re.compile(
                    r'Using an in-memory repository'
                ),
                
                'NO_USER_PROFILE': re.compile(
                    r'Neither user profile nor HKLM registry available'
                ),
                
                'NO_XML_ENCRYPTOR': re.compile(
                    r'No XML encryptor configured.*?Key\s*\{([a-f0-9\-]+)\}'
                ),
                
                'REDIRECT_PORT_FAILED': re.compile(
                    r'Failed to determine the https port for redirect'
                ),
                
                'QUERY_ORDERBY_WARNING': re.compile(
                    r'The query uses a row limiting operator.*?without an.*?OrderBy.*?operator'
                ),
                
                'INVALID_TYPE': re.compile(
                    r'Not correct type'
                ),
                
                'SENSITIVE_DATA_LOGGING': re.compile(
                    r'Sensitive data logging is enabled\. Log entries and exception messages may include sensitive application data; this mode should only be enabled during development\.'
                ),
                
                # External API patterns - Cải tiến để capture URL và error details tốt hơn
                'EXTERNAL_API_ERROR': re.compile(
                    r'(?:HttpClient|HttpClientFactory|IHttpClientFactory).*?(?:to|at|for|requesting)\s+(?:URL\s+)?["\']?([^"\'\s]+(?:://[^"\'\s]+)?)["\']?.*?(?:failed|error|exception|timeout|connection refused|bad request|unauthorized|forbidden|not found|internal server error|service unavailable)(?:\s*:\s*(.*))?',
                    re.IGNORECASE
                ),
                
                'EXTERNAL_API_TIMEOUT': re.compile(
                    r'(?:HttpClient|HttpClientFactory|IHttpClientFactory).*?(?:to|at|for|requesting)\s+(?:URL\s+)?["\']?([^"\'\s]+(?:://[^"\'\s]+)?)["\']?.*?(?:timeout|timed out|request timeout|connection timeout|OperationCanceledException)(?:\s*:\s*(.*))?',
                    re.IGNORECASE
                ),
                
                'EXTERNAL_API_HTTP_ERROR': re.compile(
                    r'(?:HttpClient|HttpClientFactory|IHttpClientFactory).*?(?:to|at|for|requesting)\s+(?:URL\s+)?["\']?([^"\'\s]+(?:://[^"\'\s]+)?)["\']?.*?(?:HTTP\s+(\d{3})|status code\s+(\d{3})|StatusCode:\s+(\d{3})|bad request|unauthorized|forbidden|not found|internal server error|service unavailable)(?:\s*:\s*(.*))?',
                    re.IGNORECASE
                ),
                
                'EXTERNAL_API_HTTPCLIENT_ERROR': re.compile(
                    r'HttpClient.*?(?:GetAsync|PostAsync|PutAsync|DeleteAsync|SendAsync).*?["\']?([^"\'\s]+(?:://[^"\'\s]+)?)["\']?.*?(?:failed|error|exception|HttpRequestException)(?:\s*:\s*(.*))?',
                    re.IGNORECASE
                ),
            }
        self.__patterns = patterns

    @property
    def patterns(self):
        return self.__patterns

    def add_pattern(self, label, pattern):
        if not isinstance(label, str):
            raise ValueError("label phải là một string")
        if not isinstance(pattern, re.Pattern):
            raise ValueError("pattern phải là một đối tượng regex đã biên dịch")
        if label in self.__patterns:
            raise ValueError(f"label '{label}' đã tồn tại")

        self.__patterns[label] = pattern

    def label_log_by_regex(self, log_line):
        """
        Labels a log line by matching it against a set of regular expressions.

        Args:
            log_line (str): The log line to label.

        Returns:
            tuple: A tuple containing the label and a dictionary of extracted data.  Returns
                   ('UNKNOWN', {}) if no match is found.
        """

        for label, pattern in self.patterns.items():
            match = pattern.search(log_line)
            if match:
                return LogLabeler._process_match(label, match)

        return 'UNLABELED', {}

    @staticmethod
    def _process_match(label, match):
        """
        Processes a regex match and returns the label and extracted data.

        Args:
            label (str): The label of the matching regex.
            match (re.Match): The match object.

        Returns:
            tuple: A tuple containing the label and a dictionary of extracted data.
        """

        if label == 'HTTP_REQUEST_DETAIL':
            timestamp, status_text, json_str = match.groups()
            try:
                json_start = json_str.find('{')
                if json_start != -1:
                    json_data = json.loads(json_str[json_start:])
                    return label, {
                        'timestamp': timestamp,
                        'status_text': status_text,
                        'status_code': json_data.get('status'),
                        'is_success': json_data.get('isSuccessStatusCode'),
                        'is_internal_server_error': json_data.get('isInternalServerError')
                    }
                else:
                    return label, {
                        'timestamp': timestamp,
                        'status_text': status_text,
                        'status_code': None
                    }
            except Exception as e:
                return label, {
                    'timestamp': timestamp,
                    'status_text': status_text,
                    'status_code': None,
                    'error': str(e)
                }

        elif label == 'HTTP_REQUEST_END':
            groups = match.groups()
            http_version = groups[0]
            method = groups[1]
            url_full = groups[2].strip()
            status_code = int(groups[3])
            content_info = groups[4]
            content_type_quoted = groups[5]
            content_type_unquoted = groups[6] 
            duration = float(groups[7])
            
            # Parse content info
            content_length = None
            if content_info.isdigit():
                content_length = int(content_info)
            elif content_info != 'null':
                content_length = content_info
            
            # Get content type
            content_type = content_type_quoted if content_type_quoted else content_type_unquoted
            if content_type == 'null':
                content_type = None
                
            return label, {
                'http_version': http_version,
                'method': method,
                'url': url_full,
                'status_code': status_code,
                'content_length': content_length,
                'content_type': content_type,
                'duration_ms': duration
            }

        elif label == 'DATABASE_QUERY':
            # duration, command_details = match.groups()
            # duration = duration.replace(',', '.')
            # sql_start = command_details.find('"""')
            # sql_command = command_details[sql_start + 3:].strip('"""') if sql_start != -1 else ''
            # return label, {
            #     'duration_ms': float(duration),
            #     'sql_command': sql_command.strip()
            # }

            duration, sql_start_word = match.groups()
            duration = float(duration.replace(',', '.'))
            return label, {
                'duration_ms': duration,
                'sql_command': sql_start_word.strip()
            }

        elif label == 'PERFORMANCE_WARNING':
            request_info, duration_ms = match.groups()
            return label, {
                'request_info': request_info.strip(),
                'duration_ms': int(duration_ms)
            }

        elif label == 'HTTP_REQUEST_START':
            http_version = match.group("http_version")
            method = match.group("method")
            raw_url = match.group("raw_url").strip()
            query_params = match.group("query_params") if match.group("query_params") else ""
            
            cleaned_url = raw_url.replace('"', '').replace(' ', '')
            return label, {
                'http_version': http_version,
                'method': method,
                'url': cleaned_url,
                'query_params': query_params.strip()
            }

        elif label in ['HTTP_REQUEST_START_PROCESSING', 'HTTP_REQUEST_SENDING']:
            method = match.group("method")
            raw_url = match.group("raw_url")
            query_params = match.group("query_params") if match.group("query_params") else ""
            
            cleaned_url = raw_url.replace('"', '').replace(' ', '')
            return label, {
                'method': method,
                'url': cleaned_url,
                'query_params': query_params.strip()
            }

        elif label in ['HTTP_RESPONSE_RECEIVED', 'HTTP_REQUEST_END_PROCESSING']:
            groups = match.groups()
            duration = groups[0]
            status_code = groups[1]
            additional_info = groups[2] if len(groups) > 2 and groups[2] else None
            
            return label, {
                'duration_ms': float(duration),
                'status_code': int(status_code),
                'additional_info': additional_info
            }

        elif label == 'API_REQUEST':
            request_info, log_action = match.groups()
            return label, {
                'request_info': request_info.strip(),
                'log_action': log_action.strip()
            }

        elif label == 'REDIRECT':
            groups = match.groups()
            redirect_to = groups[0]
            context = groups[1] if len(groups) > 1 and groups[1] else None
            return label, {
                'redirect_to': redirect_to,
                'context': context
            }

        elif label == 'STATIC_FILE':
            path, physical_path = match.groups()
            return label, {'request_path': path, 'physical_path': physical_path}

        elif label == 'FILE_NOT_MODIFIED':
            file_path, = match.groups()
            return label, {'file_path': file_path}

        elif label == 'MONGO_QUERY':
            collection_name, pipeline = match.groups()
            result = {'collection': collection_name}
            try:
                if pipeline.strip() != '"?"':
                    pipeline_data = json.loads(f'[{pipeline}]')
                    result['pipeline'] = pipeline_data
                else:
                    result['pipeline'] = []
            except json.JSONDecodeError:
                result['pipeline'] = pipeline
            return label, result

        elif label == 'AUTHZ_FAILED':
            groups = match.groups()
            requirement_detail = groups[0] if groups[0] else 'Unknown requirement'
            context = groups[1] if len(groups) > 1 and groups[1] else None
            return label, {
                'requirement_detail': requirement_detail.strip(),
                'context': context
            }

        elif label == 'AUTH_SCHEME_CHALLENGED':
            groups = match.groups()
            scheme = groups[0]
            status = groups[1]
            context = groups[2] if len(groups) > 2 and groups[2] else None
            return label, {
                'scheme': scheme,
                'status': status,
                'context': context
            }

        elif label == 'HTTP_STATUS_SET':
            groups = match.groups()
            status_code = groups[0]
            context = groups[1] if len(groups) > 1 and groups[1] else None
            return label, {
                'status_code': int(status_code),
                'context': context
            }

        elif label == 'HTTP_WRITE_JSON':
            groups = match.groups()
            json_type = groups[0]
            context = groups[1] if len(groups) > 1 and groups[1] else None
            return label, {
                'type': json_type,
                'context': context
            }

        elif label == 'KEY_CREATED':
            key_id, created, activated, expired = match.groups()
            return label, {
                'key_id': key_id,
                'created_at': created,
                'activated_at': activated,
                'expires_at': expired
            }

        elif label == 'INVALID_CAST':
            from_type, to_type = match.groups()
            return label, {
                'from_type': from_type,
                'to_type': to_type
            }

        elif label == 'TRANSACTION_BEGIN':
            max_commit_time, read_concern, read_preference, write_concern = match.groups()
            return label, {
                'max_commit_time': max_commit_time,
                'read_concern': read_concern,
                'read_preference': read_preference,
                'write_concern': write_concern
            }

        elif label == 'FILE_DOWNLOAD':
            file_name, = match.groups()
            return label, {'file_name': file_name}

        elif label == 'CHALLENGE_RESULT':
            groups = match.groups()
            schemes = groups[0]
            context = groups[1] if len(groups) > 1 and groups[1] else None
            try:
                schemes_list = json.loads(schemes.replace('[]', '[]'))
            except json.JSONDecodeError:
                schemes_list = schemes
            return label, {
                'authentication_schemes': schemes_list,
                'context': context
            }

        elif label == 'DOSSIER_COUNT_FAIL':
            filter_str, error = match.groups()
            return label, {
                'filter': filter_str,
                'error': error
            }

        elif label == 'MIDDLEWARE_PIPELINE_NOT_HANDLED':
            request_path, method, status_code = match.groups()
            return label, {
                'request_path': request_path,
                'method': method.strip(),
                'status_code': int(status_code)
            }

        elif label == 'INDEX_ERROR':
            index_name, = match.groups()
            return label, {'index_name': index_name}

        elif label == 'SEARCH_DOCUMENT_FAILED':
            groups = match.groups()
            index_name = groups[0]
            from_offset = groups[1] if groups[1] else None
            size = groups[2] if groups[2] else None
            error = groups[3]

            result = {
                'index_name': index_name,
                'error': error
            }

            if from_offset is not None:
                result['from'] = int(from_offset)
            if size is not None:
                result['size'] = int(size)

            return label, result

        elif label == 'NO_XML_ENCRYPTOR':
            key_id, = match.groups()
            return label, {'key_id': key_id}
        
        elif label == 'BULK_WRITE_UNIVERSAL':
            groups = match.groups()
            operation_type = groups[0].lower()  # 'executing' or 'executed'
            duration = float(groups[1].replace(',', '.'))
            collection = groups[2]
            
            if operation_type == 'executing':
                insertions = int(groups[3]) if groups[3] else 0
                deletions = int(groups[4]) if groups[4] else 0  
                modifications = int(groups[5]) if groups[5] else 0
                return f'BULK_WRITE_EXECUTING', {
                    'duration_ms': duration,
                    'collection': collection,
                    'insertions': insertions,
                    'deletions': deletions,
                    'modifications': modifications
                }
            else:  # executed
                inserted = int(groups[6]) if groups[6] else 0
                deleted = int(groups[7]) if groups[7] else 0
                modified = int(groups[8]) if groups[8] else 0
                return f'BULK_WRITE_EXECUTED', {
                    'duration_ms': duration,
                    'collection': collection,
                    'inserted': inserted,
                    'deleted': deleted,
                    'modified': modified
                }

        elif label in (
                'APP_STARTUP', 'ENDPOINT_EXEC', 'SYSTEM_INFO',
                'INMEMORY_REPO_USED', 'NO_USER_PROFILE',
                'REDIRECT_PORT_FAILED', 'QUERY_ORDERBY_WARNING',
                'APP_SHUTDOWN', 'INVALID_TYPE', 'SENSITIVE_DATA_LOGGING'
        ):
            return label, {}

        # External API Error Processing with URL extraction
        elif label == 'EXTERNAL_API_HTTP_ERROR':
            groups = match.groups()
            url = groups[0] if groups[0] else None
            status_code = None
            error_message = None
            
            # Tìm status code từ các groups
            for i in range(1, 4):  # groups[1], groups[2], groups[3]
                if i < len(groups) and groups[i] and groups[i].isdigit():
                    status_code = int(groups[i])
                    break
            
            # Error message là group cuối cùng
            if len(groups) > 4 and groups[4]:
                error_message = groups[4]
            
            return label, {
                'url': url,
                'status_code': status_code,
                'error_type': 'http_error',
                'error_message': error_message,
                'message': match.group(0)
            }

        elif label in [
            'EXTERNAL_API_ERROR', 'EXTERNAL_API_TIMEOUT', 
            'EXTERNAL_API_HTTPCLIENT_ERROR'
        ]:
            groups = match.groups()
            url = groups[0] if groups[0] else None
            error_message = groups[1] if len(groups) > 1 and groups[1] else None
            error_type = label.lower().replace('external_api_', '')
            
            # Extract service name from URL if available
            service_name = None
            if url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    service_name = parsed.netloc
                except:
                    service_name = url
            
            return label, {
                'url': url,
                'service_name': service_name,
                'error_type': error_type,
                'error_message': error_message,
                'message': match.group(0),
                'full_message': match.group(0)
            }


        else:
            return label, {'message': match.group(0)}
        

def get_label_log(msg):
    loglabel = LogLabeler()
    cln_msg = clean_log_message(msg=msg)
    label, data = loglabel.label_log_by_regex(log_line=cln_msg)
    return label, data