import json
import csv
import sys

def convert_deepeval_to_csv(json_file, csv_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    rows = []
    
    # Handle cache file format
    if 'test_cases_lookup_map' in data:
        test_case_counter = 1
        for test_key, test_data in data['test_cases_lookup_map'].items():
            test_input = json.loads(test_key)
            for cached_metric in test_data['cached_metrics_data']:
                metric = cached_metric['metric_data']
                rows.append({
                    'test_case': f'test_case{test_case_counter}',
                    'prompt': test_input['input'],
                    'success': metric['success'],
                    'metric_name': metric['name'],
                    'metric_score': metric['score'],
                    'metric_threshold': metric['threshold'],
                    'metric_success': metric['success'],
                    'metric_reason': metric['reason'][:200] + '...' if len(metric['reason']) > 200 else metric['reason']
                })
            test_case_counter += 1
        
        # Write to CSV and return early for cache files
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['test_case', 'prompt', 'success', 'metric_name', 'metric_score', 'metric_threshold', 'metric_success', 'metric_reason'])
            writer.writeheader()
            writer.writerows(rows)
        return
    
    # Process conversational test cases
    for i, test_case in enumerate(data['testRunData']['conversationalTestCases']):
        for metric in test_case['metricsData']:
            rows.append({
                'test_case': f"conversational_{i}",
                'test_name': test_case['name'],
                'success': test_case['success'],
                'metric_name': metric['name'],
                'metric_score': metric['score'],
                'metric_threshold': metric['threshold'],
                'metric_success': metric['success'],
                'metric_reason': metric['reason'][:200] + '...' if len(metric['reason']) > 200 else metric['reason']
            })
    
    # Process regular test cases
    for i, test_case in enumerate(data['testRunData']['testCases']):
        for metric in test_case.get('metricsData', []):
            rows.append({
                'test_case': f"regular_{i}",
                'test_name': test_case.get('name', f'test_{i}'),
                'success': test_case.get('success', False),
                'metric_name': metric['name'],
                'metric_score': metric['score'],
                'metric_threshold': metric['threshold'],
                'metric_success': metric['success'],
                'metric_reason': metric['reason'][:200] + '...' if len(metric['reason']) > 200 else metric['reason']
            })
    
    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['test_case', 'test_name', 'success', 'metric_name', 'metric_score', 'metric_threshold', 'metric_success', 'metric_reason'])
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    convert_deepeval_to_csv('.deepeval/.latest_test_run.json', 'deepeval_results.csv')
    print("Converted to deepeval_results.csv")
    
    convert_deepeval_to_csv('.deepeval/.deepeval-cache.json', 'deepeval_cache.csv')
    print("Converted cache to deepeval_cache.csv")