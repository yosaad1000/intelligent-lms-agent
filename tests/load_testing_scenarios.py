"""
Load Testing Scenarios for LMS API Performance
Comprehensive load testing with realistic user scenarios
"""

import asyncio
import aiohttp
import time
import json
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Results from a load test scenario"""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    duration_seconds: float
    errors: List[str]


@dataclass
class UserScenario:
    """Represents a user scenario for load testing"""
    user_id: str
    scenario_type: str
    actions: List[Dict[str, Any]]
    think_time_ms: int = 1000  # Time between actions


class LoadTestRunner:
    """
    Comprehensive load testing runner for LMS API
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize load test runner"""
        
        self.base_url = base_url.rstrip('/')
        self.session = None
        
        # Test data
        self.test_users = [f"load_test_user_{i}" for i in range(100)]
        self.test_documents = [
            "Machine Learning Fundamentals.pdf",
            "Python Programming Guide.docx",
            "Data Science Handbook.pdf",
            "AI Ethics and Society.txt",
            "Deep Learning Concepts.pdf"
        ]
        self.test_topics = [
            "machine learning",
            "python programming",
            "data science",
            "artificial intelligence",
            "deep learning"
        ]
    
    async def setup_session(self):
        """Setup HTTP session for load testing"""
        
        connector = aiohttp.TCPConnector(
            limit=200,  # Total connection pool size
            limit_per_host=50,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,  # Total timeout
            connect=10,  # Connection timeout
            sock_read=20  # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'LMS-LoadTest/1.0'
            }
        )
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        
        if self.session:
            await self.session.close()
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with timing and error handling"""
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if user_id:
            headers['X-User-ID'] = user_id
        
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    response_data = await response.json()
                    status_code = response.status
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json()
                    status_code = response.status
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                'success': 200 <= status_code < 400,
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'response_data': response_data,
                'error': None
            }
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                'success': False,
                'status_code': 0,
                'response_time_ms': response_time_ms,
                'response_data': None,
                'error': str(e)
            }
    
    async def simulate_user_session(self, user_scenario: UserScenario) -> List[Dict[str, Any]]:
        """Simulate a complete user session"""
        
        results = []
        
        for action in user_scenario.actions:
            # Execute action
            result = await self.make_request(
                method=action['method'],
                endpoint=action['endpoint'],
                data=action.get('data'),
                user_id=user_scenario.user_id
            )
            
            result['action'] = action['name']
            result['user_id'] = user_scenario.user_id
            result['timestamp'] = datetime.utcnow().isoformat()
            
            results.append(result)
            
            # Think time between actions
            if user_scenario.think_time_ms > 0:
                await asyncio.sleep(user_scenario.think_time_ms / 1000)
        
        return results
    
    def generate_student_scenario(self, user_id: str) -> UserScenario:
        """Generate realistic student user scenario"""
        
        actions = [
            # Login/Authentication
            {
                'name': 'health_check',
                'method': 'GET',
                'endpoint': '/api/health'
            },
            
            # Upload document
            {
                'name': 'upload_document',
                'method': 'POST',
                'endpoint': '/api/files',
                'data': {
                    'filename': random.choice(self.test_documents),
                    'content_type': 'application/pdf',
                    'size': random.randint(100000, 5000000)
                }
            },
            
            # Get user files
            {
                'name': 'get_user_files',
                'method': 'GET',
                'endpoint': '/api/files'
            },
            
            # Chat with AI about document
            {
                'name': 'ai_chat_question',
                'method': 'POST',
                'endpoint': '/api/chat',
                'data': {
                    'message': f"Can you explain the key concepts in {random.choice(self.test_topics)}?",
                    'conversation_id': f"conv_{user_id}_{int(time.time())}"
                }
            },
            
            # Follow-up chat
            {
                'name': 'ai_chat_followup',
                'method': 'POST',
                'endpoint': '/api/chat',
                'data': {
                    'message': "Can you give me some examples?",
                    'conversation_id': f"conv_{user_id}_{int(time.time())}"
                }
            },
            
            # Generate quiz
            {
                'name': 'generate_quiz',
                'method': 'POST',
                'endpoint': '/api/quiz/generate',
                'data': {
                    'topic': random.choice(self.test_topics),
                    'difficulty': random.choice(['easy', 'medium', 'hard']),
                    'question_count': random.randint(5, 10)
                }
            },
            
            # Get chat history
            {
                'name': 'get_chat_history',
                'method': 'GET',
                'endpoint': '/api/chat/history'
            },
            
            # Get learning analytics
            {
                'name': 'get_analytics',
                'method': 'GET',
                'endpoint': '/api/analytics/progress'
            }
        ]
        
        return UserScenario(
            user_id=user_id,
            scenario_type='student',
            actions=actions,
            think_time_ms=random.randint(500, 2000)  # 0.5-2 seconds think time
        )
    
    def generate_teacher_scenario(self, user_id: str) -> UserScenario:
        """Generate realistic teacher user scenario"""
        
        actions = [
            # Health check
            {
                'name': 'health_check',
                'method': 'GET',
                'endpoint': '/api/health'
            },
            
            # Upload course material
            {
                'name': 'upload_course_material',
                'method': 'POST',
                'endpoint': '/api/files',
                'data': {
                    'filename': f"Course_Material_{random.choice(self.test_topics)}.pdf",
                    'content_type': 'application/pdf',
                    'size': random.randint(1000000, 10000000)
                }
            },
            
            # Create assignment quiz
            {
                'name': 'create_assignment_quiz',
                'method': 'POST',
                'endpoint': '/api/quiz/generate',
                'data': {
                    'topic': random.choice(self.test_topics),
                    'difficulty': 'medium',
                    'question_count': 15,
                    'assignment_mode': True
                }
            },
            
            # Get student analytics
            {
                'name': 'get_student_analytics',
                'method': 'GET',
                'endpoint': '/api/analytics/students'
            },
            
            # Get class performance
            {
                'name': 'get_class_performance',
                'method': 'GET',
                'endpoint': '/api/analytics/class-performance'
            },
            
            # Chat with AI for teaching assistance
            {
                'name': 'teacher_ai_chat',
                'method': 'POST',
                'endpoint': '/api/chat',
                'data': {
                    'message': f"How can I better explain {random.choice(self.test_topics)} to my students?",
                    'conversation_id': f"teacher_conv_{user_id}_{int(time.time())}"
                }
            }
        ]
        
        return UserScenario(
            user_id=user_id,
            scenario_type='teacher',
            actions=actions,
            think_time_ms=random.randint(1000, 3000)  # 1-3 seconds think time
        )
    
    async def run_concurrent_users_test(
        self,
        concurrent_users: int,
        test_duration_seconds: int = 300,
        user_mix: Dict[str, float] = None
    ) -> LoadTestResult:
        """Run concurrent users load test"""
        
        if user_mix is None:
            user_mix = {'student': 0.8, 'teacher': 0.2}  # 80% students, 20% teachers
        
        logger.info(f"Starting concurrent users test: {concurrent_users} users for {test_duration_seconds}s")
        
        # Generate user scenarios
        scenarios = []
        for i in range(concurrent_users):
            user_id = f"load_user_{i}"
            
            if random.random() < user_mix['student']:
                scenario = self.generate_student_scenario(user_id)
            else:
                scenario = self.generate_teacher_scenario(user_id)
            
            scenarios.append(scenario)
        
        # Run test
        start_time = time.time()
        all_results = []
        
        # Create tasks for concurrent execution
        tasks = []
        for scenario in scenarios:
            task = asyncio.create_task(self.simulate_user_session(scenario))
            tasks.append(task)
        
        # Wait for all tasks to complete or timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=test_duration_seconds + 60  # Extra buffer
            )
            
            # Flatten results
            for result_set in results:
                if isinstance(result_set, list):
                    all_results.extend(result_set)
                elif isinstance(result_set, Exception):
                    logger.error(f"Task failed with exception: {result_set}")
        
        except asyncio.TimeoutError:
            logger.warning("Load test timed out")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        end_time = time.time()
        
        # Calculate results
        return self._calculate_load_test_results(
            scenario_name=f"concurrent_users_{concurrent_users}",
            results=all_results,
            duration_seconds=end_time - start_time
        )
    
    async def run_ramp_up_test(
        self,
        max_users: int,
        ramp_up_duration_seconds: int = 300,
        hold_duration_seconds: int = 300
    ) -> LoadTestResult:
        """Run ramp-up load test"""
        
        logger.info(f"Starting ramp-up test: 0 to {max_users} users over {ramp_up_duration_seconds}s")
        
        all_results = []
        start_time = time.time()
        
        # Calculate ramp-up rate
        users_per_second = max_users / ramp_up_duration_seconds
        
        active_tasks = []
        
        # Ramp-up phase
        for second in range(ramp_up_duration_seconds):
            # Add new users
            new_users = int((second + 1) * users_per_second) - int(second * users_per_second)
            
            for _ in range(new_users):
                user_id = f"ramp_user_{len(active_tasks)}"
                scenario = self.generate_student_scenario(user_id)
                
                task = asyncio.create_task(self.simulate_user_session(scenario))
                active_tasks.append(task)
            
            await asyncio.sleep(1)
        
        logger.info(f"Ramp-up complete. Holding {len(active_tasks)} users for {hold_duration_seconds}s")
        
        # Hold phase - wait for existing tasks and start new ones
        hold_start = time.time()
        while time.time() - hold_start < hold_duration_seconds:
            # Check for completed tasks
            done_tasks = [task for task in active_tasks if task.done()]
            
            for task in done_tasks:
                try:
                    result = await task
                    if isinstance(result, list):
                        all_results.extend(result)
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                
                active_tasks.remove(task)
                
                # Start new user to maintain load
                user_id = f"hold_user_{int(time.time())}"
                scenario = self.generate_student_scenario(user_id)
                new_task = asyncio.create_task(self.simulate_user_session(scenario))
                active_tasks.append(new_task)
            
            await asyncio.sleep(1)
        
        # Wait for remaining tasks
        if active_tasks:
            try:
                remaining_results = await asyncio.wait_for(
                    asyncio.gather(*active_tasks, return_exceptions=True),
                    timeout=60
                )
                
                for result in remaining_results:
                    if isinstance(result, list):
                        all_results.extend(result)
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete in time")
        
        end_time = time.time()
        
        return self._calculate_load_test_results(
            scenario_name=f"ramp_up_{max_users}_users",
            results=all_results,
            duration_seconds=end_time - start_time
        )
    
    async def run_spike_test(
        self,
        baseline_users: int = 10,
        spike_users: int = 100,
        spike_duration_seconds: int = 60
    ) -> LoadTestResult:
        """Run spike load test"""
        
        logger.info(f"Starting spike test: {baseline_users} baseline, spike to {spike_users} for {spike_duration_seconds}s")
        
        all_results = []
        start_time = time.time()
        
        # Start baseline load
        baseline_tasks = []
        for i in range(baseline_users):
            user_id = f"baseline_user_{i}"
            scenario = self.generate_student_scenario(user_id)
            task = asyncio.create_task(self.simulate_user_session(scenario))
            baseline_tasks.append(task)
        
        # Wait a bit for baseline to establish
        await asyncio.sleep(30)
        
        # Create spike load
        spike_tasks = []
        for i in range(spike_users - baseline_users):
            user_id = f"spike_user_{i}"
            scenario = self.generate_student_scenario(user_id)
            task = asyncio.create_task(self.simulate_user_session(scenario))
            spike_tasks.append(task)
        
        # Wait for spike duration
        await asyncio.sleep(spike_duration_seconds)
        
        # Collect results from all tasks
        all_tasks = baseline_tasks + spike_tasks
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*all_tasks, return_exceptions=True),
                timeout=120
            )
            
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
        except asyncio.TimeoutError:
            logger.warning("Spike test timed out")
        
        end_time = time.time()
        
        return self._calculate_load_test_results(
            scenario_name=f"spike_{spike_users}_users",
            results=all_results,
            duration_seconds=end_time - start_time
        )
    
    async def run_performance_optimization_test(self) -> LoadTestResult:
        """Test performance optimization features under load"""
        
        logger.info("Starting performance optimization test")
        
        all_results = []
        start_time = time.time()
        
        # Test performance endpoints with concurrent requests
        performance_scenarios = [
            # Cache operations
            {
                'name': 'cache_set',
                'method': 'POST',
                'endpoint': '/api/performance/cache',
                'data': {
                    'operation': 'set',
                    'prefix': 'load_test',
                    'key': f'test_key_{int(time.time())}',
                    'value': {'test': 'performance_data', 'timestamp': time.time()},
                    'ttl_seconds': 300
                }
            },
            {
                'name': 'cache_get',
                'method': 'POST',
                'endpoint': '/api/performance/cache',
                'data': {
                    'operation': 'get',
                    'prefix': 'load_test',
                    'key': 'test_key_123'
                }
            },
            # Performance metrics
            {
                'name': 'performance_metrics',
                'method': 'GET',
                'endpoint': '/api/performance/metrics?hours=1'
            },
            # Performance health
            {
                'name': 'performance_health',
                'method': 'GET',
                'endpoint': '/api/performance/health'
            },
            # System optimization
            {
                'name': 'system_optimization',
                'method': 'POST',
                'endpoint': '/api/performance/optimize',
                'data': {}
            }
        ]
        
        # Create concurrent tasks for performance testing
        tasks = []
        
        for i in range(30):  # 30 concurrent performance operations
            scenario = random.choice(performance_scenarios)
            user_id = f"perf_user_{i % 10}"  # 10 different users
            
            # Create user scenario for performance testing
            user_scenario = UserScenario(
                user_id=user_id,
                scenario_type='performance_test',
                actions=[scenario],
                think_time_ms=100  # Fast operations for performance testing
            )
            
            task = asyncio.create_task(self.simulate_user_session(user_scenario))
            tasks.append(task)
        
        # Execute all performance tests concurrently
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=120  # 2 minute timeout
            )
            
            # Flatten results
            for result_set in results:
                if isinstance(result_set, list):
                    all_results.extend(result_set)
                elif isinstance(result_set, Exception):
                    logger.error(f"Performance test task failed: {result_set}")
        
        except asyncio.TimeoutError:
            logger.warning("Performance optimization test timed out")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        end_time = time.time()
        
        return self._calculate_load_test_results(
            scenario_name="performance_optimization",
            results=all_results,
            duration_seconds=end_time - start_time
        )
    
    def _calculate_load_test_results(
        self,
        scenario_name: str,
        results: List[Dict[str, Any]],
        duration_seconds: float
    ) -> LoadTestResult:
        """Calculate load test results from raw data"""
        
        if not results:
            return LoadTestResult(
                scenario_name=scenario_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                error_rate_percent=0,
                duration_seconds=duration_seconds,
                errors=[]
            )
        
        # Basic counts
        total_requests = len(results)
        successful_requests = len([r for r in results if r['success']])
        failed_requests = total_requests - successful_requests
        
        # Response times
        response_times = [r['response_time_ms'] for r in results]
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Percentiles
        sorted_times = sorted(response_times)
        p95_index = int(0.95 * len(sorted_times))
        p99_index = int(0.99 * len(sorted_times))
        p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
        p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        
        # Rates
        requests_per_second = total_requests / duration_seconds if duration_seconds > 0 else 0
        error_rate_percent = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Collect errors
        errors = [r['error'] for r in results if r['error']]
        unique_errors = list(set(errors))
        
        return LoadTestResult(
            scenario_name=scenario_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate_percent=error_rate_percent,
            duration_seconds=duration_seconds,
            errors=unique_errors[:10]  # Limit to first 10 unique errors
        )
    
    def print_results(self, result: LoadTestResult):
        """Print formatted load test results"""
        
        print(f"\n{'='*60}")
        print(f"Load Test Results: {result.scenario_name}")
        print(f"{'='*60}")
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate_percent:.2f}%")
        print(f"Requests/Second: {result.requests_per_second:.2f}")
        print(f"\nResponse Times (ms):")
        print(f"  Average: {result.avg_response_time_ms:.2f}")
        print(f"  Minimum: {result.min_response_time_ms:.2f}")
        print(f"  Maximum: {result.max_response_time_ms:.2f}")
        print(f"  95th Percentile: {result.p95_response_time_ms:.2f}")
        print(f"  99th Percentile: {result.p99_response_time_ms:.2f}")
        
        if result.errors:
            print(f"\nTop Errors:")
            for i, error in enumerate(result.errors[:5], 1):
                print(f"  {i}. {error}")
        
        print(f"{'='*60}\n")
    
    async def run_comprehensive_load_test(self) -> Dict[str, LoadTestResult]:
        """Run comprehensive load testing suite"""
        
        logger.info("Starting comprehensive load testing suite")
        
        await self.setup_session()
        
        try:
            results = {}
            
            # Test 1: Light load (10 concurrent users)
            logger.info("Running light load test...")
            results['light_load'] = await self.run_concurrent_users_test(
                concurrent_users=10,
                test_duration_seconds=120
            )
            self.print_results(results['light_load'])
            
            # Test 2: Medium load (50 concurrent users)
            logger.info("Running medium load test...")
            results['medium_load'] = await self.run_concurrent_users_test(
                concurrent_users=50,
                test_duration_seconds=180
            )
            self.print_results(results['medium_load'])
            
            # Test 3: Heavy load (100 concurrent users)
            logger.info("Running heavy load test...")
            results['heavy_load'] = await self.run_concurrent_users_test(
                concurrent_users=100,
                test_duration_seconds=240
            )
            self.print_results(results['heavy_load'])
            
            # Test 4: Ramp-up test
            logger.info("Running ramp-up test...")
            results['ramp_up'] = await self.run_ramp_up_test(
                max_users=75,
                ramp_up_duration_seconds=120,
                hold_duration_seconds=180
            )
            self.print_results(results['ramp_up'])
            
            # Test 5: Spike test
            logger.info("Running spike test...")
            results['spike'] = await self.run_spike_test(
                baseline_users=20,
                spike_users=150,
                spike_duration_seconds=60
            )
            self.print_results(results['spike'])
            
            # Test 6: Performance optimization test
            logger.info("Running performance optimization test...")
            results['performance_optimization'] = await self.run_performance_optimization_test()
            self.print_results(results['performance_optimization'])
            
            return results
            
        finally:
            await self.cleanup_session()


async def main():
    """Main function to run load tests"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"  # Change to your API URL
    
    # Create load test runner
    runner = LoadTestRunner(base_url=BASE_URL)
    
    # Run comprehensive load tests
    results = await runner.run_comprehensive_load_test()
    
    # Generate summary report
    print("\n" + "="*80)
    print("LOAD TEST SUMMARY REPORT")
    print("="*80)
    
    for test_name, result in results.items():
        print(f"\n{test_name.upper()}:")
        print(f"  Requests/sec: {result.requests_per_second:.2f}")
        print(f"  Avg Response: {result.avg_response_time_ms:.2f}ms")
        print(f"  Error Rate: {result.error_rate_percent:.2f}%")
        print(f"  P95 Response: {result.p95_response_time_ms:.2f}ms")
    
    # Performance recommendations
    print("\n" + "="*80)
    print("PERFORMANCE RECOMMENDATIONS")
    print("="*80)
    
    # Analyze results and provide recommendations
    heavy_load = results.get('heavy_load')
    if heavy_load:
        if heavy_load.avg_response_time_ms > 3000:
            print("⚠️  High average response time detected. Consider:")
            print("   - Implementing response caching")
            print("   - Optimizing database queries")
            print("   - Adding connection pooling")
        
        if heavy_load.error_rate_percent > 5:
            print("⚠️  High error rate detected. Consider:")
            print("   - Implementing circuit breakers")
            print("   - Adding retry logic")
            print("   - Improving error handling")
        
        if heavy_load.requests_per_second < 10:
            print("⚠️  Low throughput detected. Consider:")
            print("   - Scaling infrastructure")
            print("   - Optimizing application code")
            print("   - Implementing async processing")
    
    print("\n✅ Load testing completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())