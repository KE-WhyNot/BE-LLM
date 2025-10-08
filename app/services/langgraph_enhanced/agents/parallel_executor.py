"""
병렬 실행 에이전트
여러 에이전트를 동시에 실행하여 시간 효율성 향상
"""

import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelExecutor:
    """⚡ 병렬 실행 에이전트"""
    
    def __init__(self):
        self.agent_name = "parallel_executor"
        self.max_workers = 5  # 최대 동시 실행 에이전트 수
    
    async def execute_parallel(
        self, 
        agent_groups: List[List[str]], 
        agents_dict: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """병렬 그룹 실행"""
        try:
            results = {
                'success': True,
                'agent_results': {},
                'execution_time': 0.0,
                'parallel_groups_executed': len(agent_groups)
            }
            
            import time
            start_time = time.time()
            
            for group_idx, agent_group in enumerate(agent_groups):
                print(f"⚡ 병렬 그룹 {group_idx + 1} 실행: {agent_group}")
                
                # 그룹 내 에이전트들을 병렬로 실행
                group_results = await self._execute_group(
                    agent_group, 
                    agents_dict, 
                    state
                )
                
                # 결과 통합
                results['agent_results'].update(group_results)
                
                print(f"✅ 병렬 그룹 {group_idx + 1} 완료")
            
            results['execution_time'] = time.time() - start_time
            print(f"⚡ 전체 병렬 실행 완료: {results['execution_time']:.2f}초")
            
            return results
            
        except Exception as e:
            print(f"❌ 병렬 실행 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_results': {},
                'execution_time': 0.0
            }
    
    async def _execute_group(
        self, 
        agent_names: List[str], 
        agents_dict: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 병렬 그룹 실행"""
        tasks = []
        
        for agent_name in agent_names:
            if agent_name in agents_dict:
                task = self._execute_agent_async(
                    agent_name, 
                    agents_dict[agent_name], 
                    state
                )
                tasks.append(task)
        
        # 모든 태스크를 병렬로 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        group_results = {}
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                print(f"❌ {agent_name} 실행 오류: {result}")
                group_results[agent_name] = {
                    'success': False,
                    'error': str(result)
                }
            else:
                group_results[agent_name] = result
        
        return group_results
    
    async def _execute_agent_async(
        self, 
        agent_name: str, 
        agent: Any, 
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """비동기 에이전트 실행"""
        try:
            print(f"   🔄 {agent_name} 시작...")
            
            # 에이전트 실행 (동기 함수를 비동기로 래핑)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._execute_agent_sync,
                agent,
                state
            )
            
            print(f"   ✅ {agent_name} 완료")
            return result
            
        except Exception as e:
            print(f"   ❌ {agent_name} 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_name': agent_name
            }
    
    def _execute_agent_sync(self, agent: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """동기 에이전트 실행"""
        try:
            user_query = state.get('user_query', '')
            query_analysis = state.get('query_analysis', {})
            
            # 에이전트의 process 메서드 호출
            if hasattr(agent, 'process'):
                result = agent.process(user_query, query_analysis)
                return result
            else:
                return {
                    'success': False,
                    'error': 'Agent does not have process method'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_parallel_sync(
        self, 
        agent_groups: List[List[str]], 
        agents_dict: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """동기 버전 병렬 실행 (ThreadPoolExecutor 사용)"""
        try:
            results = {
                'success': True,
                'agent_results': {},
                'execution_time': 0.0,
                'parallel_groups_executed': len(agent_groups)
            }
            
            import time
            start_time = time.time()
            
            for group_idx, agent_group in enumerate(agent_groups):
                print(f"⚡ 병렬 그룹 {group_idx + 1} 실행: {agent_group}")
                
                # ThreadPoolExecutor로 병렬 실행
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {}
                    
                    for agent_name in agent_group:
                        if agent_name in agents_dict:
                            future = executor.submit(
                                self._execute_agent_sync,
                                agents_dict[agent_name],
                                state
                            )
                            futures[future] = agent_name
                    
                    # 결과 수집
                    for future in as_completed(futures):
                        agent_name = futures[future]
                        try:
                            result = future.result()
                            results['agent_results'][agent_name] = result
                            print(f"   ✅ {agent_name} 완료")
                        except Exception as e:
                            print(f"   ❌ {agent_name} 오류: {e}")
                            results['agent_results'][agent_name] = {
                                'success': False,
                                'error': str(e)
                            }
                
                print(f"✅ 병렬 그룹 {group_idx + 1} 완료")
            
            results['execution_time'] = time.time() - start_time
            print(f"⚡ 전체 병렬 실행 완료: {results['execution_time']:.2f}초")
            
            return results
            
        except Exception as e:
            print(f"❌ 병렬 실행 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_results': {},
                'execution_time': 0.0
            }


# 싱글톤 인스턴스
parallel_executor = ParallelExecutor()

