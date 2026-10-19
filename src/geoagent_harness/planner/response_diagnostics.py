"""Safe response-shape findings; never log model output or parser input excerpts."""
import json


class TruncatedModelReply(ValueError):
    pass


def response_diagnostics(result):
    text = result.content
    finish = result.finish_reason
    safe_finish = finish if finish in {'stop', 'length', 'content_filter', 'tool_calls', 'function_call', None} else 'other'
    try:
        value = json.loads(text)
        shape = ('object' if isinstance(value, dict) else 'array' if isinstance(value, list)
                 else 'null' if value is None else 'string' if isinstance(value, str) else 'scalar')
    except (ValueError, RecursionError):
        shape = 'markdown_fence' if text.lstrip().startswith('```') else 'reasoning_prefix' if text.lstrip().startswith('<think>') else 'invalid_json'
    return {'response_bytes': len(text.encode('utf-8')), 'response_shape': shape,
            'finish_reason': safe_finish, 'response_format': result.response_format,
            'completion_tokens': result.completion_tokens}
