#!/usr/bin/env python3
"""
Marine Data Integration Platform - Test Runner
Comprehensive test suite runner for all platform components
"""

import os
import sys
import unittest
import argparse
from pathlib import Path
import json
from datetime import datetime
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))


class TestRunner:
    """Comprehensive test runner for the marine platform"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'test_suites': {},
            'start_time': None,
            'end_time': None,
            'duration': 0
        }
    
    def discover_and_run_tests(self, test_dir='tests', pattern='test_*.py', verbosity=2):
        """Discover and run all tests"""
        print("🧪 Marine Data Integration Platform - Comprehensive Test Suite")
        print("=" * 70)
        
        self.results['start_time'] = datetime.now()
        
        # Discover all test modules
        loader = unittest.TestLoader()
        
        if os.path.exists(test_dir):
            suite = loader.discover(test_dir, pattern=pattern)
        else:
            # Fallback to current directory if tests directory doesn't exist
            suite = loader.discover('.', pattern=pattern)
        
        # Run tests with custom result handler
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        result = runner.run(suite)
        
        self.results['end_time'] = datetime.now()
        self.results['duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()
        
        # Collect results
        self.results['total_tests'] = result.testsRun
        self.results['passed'] = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        self.results['failed'] = len(result.failures)
        self.results['errors'] = len(result.errors)
        self.results['skipped'] = len(result.skipped)
        
        return result
    
    def run_individual_tests(self, test_modules, verbosity=2):
        """Run specific test modules"""
        print("🧪 Running Individual Test Modules")
        print("=" * 50)
        
        self.results['start_time'] = datetime.now()
        total_result = unittest.TestResult()
        
        for module_name in test_modules:
            print(f"\n🔍 Running {module_name}...")
            
            try:
                # Import and run the module
                module = __import__(module_name, fromlist=[''])
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)
                
                runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
                result = runner.run(suite)
                
                # Aggregate results
                total_result.testsRun += result.testsRun
                total_result.failures.extend(result.failures)
                total_result.errors.extend(result.errors)
                total_result.skipped.extend(result.skipped)
                
                # Store individual module results
                self.results['test_suites'][module_name] = {
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'skipped': len(result.skipped),
                    'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
                }
                
            except Exception as e:
                print(f"❌ Failed to run {module_name}: {e}")
                total_result.errors.append((module_name, traceback.format_exc()))
        
        self.results['end_time'] = datetime.now()
        self.results['duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()
        
        # Update totals
        self.results['total_tests'] = total_result.testsRun
        self.results['passed'] = total_result.testsRun - len(total_result.failures) - len(total_result.errors) - len(total_result.skipped)
        self.results['failed'] = len(total_result.failures)
        self.results['errors'] = len(total_result.errors)
        self.results['skipped'] = len(total_result.skipped)
        
        return total_result
    
    def run_unit_tests(self, verbosity=2):
        """Run only unit tests"""
        print("🧪 Running Unit Tests")
        print("=" * 30)
        
        test_modules = [
            'tests.test_file_upload',
            'tests.test_edna_analysis'
        ]
        
        return self.run_individual_tests(test_modules, verbosity)
    
    def run_integration_tests(self, verbosity=2):
        """Run only integration tests"""
        print("🧪 Running Integration Tests")  
        print("=" * 35)
        
        test_modules = [
            'tests.test_api_integration',
            'test_api_endpoints'  # Existing integration test
        ]
        
        return self.run_individual_tests(test_modules, verbosity)
    
    def run_database_tests(self, verbosity=2):
        """Run database-specific tests"""
        print("🧪 Running Database Tests")
        print("=" * 30)
        
        test_modules = [
            'database.test_schemas'
        ]
        
        return self.run_individual_tests(test_modules, verbosity)
    
    def generate_report(self, save_to_file=True):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Overall statistics
        success_rate = (self.results['passed'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   Passed: {self.results['passed']} ✅")
        print(f"   Failed: {self.results['failed']} ❌") 
        print(f"   Errors: {self.results['errors']} 💥")
        print(f"   Skipped: {self.results['skipped']} ⏭️")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Duration: {self.results['duration']:.2f} seconds")
        
        # Individual test suite results
        if self.results['test_suites']:
            print(f"\n📋 Test Suite Breakdown:")
            for suite_name, suite_results in self.results['test_suites'].items():
                status = "✅" if suite_results['failures'] == 0 and suite_results['errors'] == 0 else "❌"
                print(f"   {suite_name:<30} {status} {suite_results['success_rate']:.1f}% ({suite_results['tests_run']} tests)")
        
        # Performance assessment
        print(f"\n⚡ Performance Assessment:")
        if self.results['total_tests'] == 0:
            print("   No tests were run")
        elif success_rate >= 95:
            print("   🎉 EXCELLENT: All systems functioning perfectly!")
        elif success_rate >= 85:
            print("   ✅ GOOD: Platform is stable with minor issues")
        elif success_rate >= 70:
            print("   ⚠️  ACCEPTABLE: Some issues need attention")
        elif success_rate >= 50:
            print("   🔧 NEEDS WORK: Significant issues detected")
        else:
            print("   🚨 CRITICAL: Major problems require immediate attention")
        
        # Component status
        print(f"\n🔧 Component Status:")
        components = {
            'File Upload & Processing': ['test_file_upload'],
            'eDNA Analysis': ['test_edna_analysis'], 
            'API Integration': ['test_api_integration'],
            'Database Operations': ['test_schemas']
        }
        
        for component, test_modules in components.items():
            component_success = True
            for module in test_modules:
                if module in self.results.get('test_suites', {}):
                    suite = self.results['test_suites'][module]
                    if suite['failures'] > 0 or suite['errors'] > 0:
                        component_success = False
                        break
            
            status = "✅ Operational" if component_success else "❌ Issues Detected"
            print(f"   {component:<25} {status}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if success_rate >= 95:
            print("   - Platform is ready for production deployment")
            print("   - Consider adding more edge case tests")
            print("   - Monitor performance in production environment")
        elif success_rate >= 85:
            print("   - Address failing tests before deployment")
            print("   - Review error logs for improvement opportunities")
            print("   - Consider stress testing under load")
        elif success_rate >= 70:
            print("   - Fix critical issues before proceeding")
            print("   - Improve error handling and validation")
            print("   - Add more comprehensive test coverage")
        else:
            print("   - Conduct thorough code review")
            print("   - Fix fundamental issues in core components")
            print("   - Consider refactoring problematic modules")
        
        print("\n" + "=" * 70)
        
        # Save report to file
        if save_to_file:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'success_rate': success_rate,
                'recommendations': self._get_recommendations(success_rate)
            }
            
            report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"📄 Detailed report saved to: {report_file}")
        
        return success_rate >= 70  # Return success if 70% or better
    
    def _get_recommendations(self, success_rate):
        """Get recommendations based on success rate"""
        if success_rate >= 95:
            return [
                "Platform is ready for production deployment",
                "Consider adding more edge case tests", 
                "Monitor performance in production environment"
            ]
        elif success_rate >= 85:
            return [
                "Address failing tests before deployment",
                "Review error logs for improvement opportunities",
                "Consider stress testing under load"
            ]
        elif success_rate >= 70:
            return [
                "Fix critical issues before proceeding",
                "Improve error handling and validation",
                "Add more comprehensive test coverage"
            ]
        else:
            return [
                "Conduct thorough code review",
                "Fix fundamental issues in core components",
                "Consider refactoring problematic modules"
            ]


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Marine Platform Test Runner")
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'database'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbosity', type=int, choices=[0, 1, 2], default=2,
                       help='Test output verbosity')
    parser.add_argument('--pattern', default='test_*.py',
                       help='Test file pattern to match')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip generating test report')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        # Run the specified type of tests
        if args.type == 'all':
            runner.discover_and_run_tests(verbosity=args.verbosity, pattern=args.pattern)
        elif args.type == 'unit':
            runner.run_unit_tests(verbosity=args.verbosity)
        elif args.type == 'integration':
            runner.run_integration_tests(verbosity=args.verbosity)
        elif args.type == 'database':
            runner.run_database_tests(verbosity=args.verbosity)
        
        # Generate report
        if not args.no_report:
            success = runner.generate_report()
            return 0 if success else 1
        else:
            success_rate = (runner.results['passed'] / runner.results['total_tests'] * 100) if runner.results['total_tests'] > 0 else 0
            return 0 if success_rate >= 70 else 1
    
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())