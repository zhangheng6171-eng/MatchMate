"""
Supabase REST API 客户端
使用 Service Role Key 通过 HTTP API 操作数据库
适用于 Vercel Serverless 等无法直连数据库的环境
"""
from typing import Any, Optional
import httpx

from app.core.config import settings


class SupabaseClient:
    """Supabase REST API 封装"""

    def __init__(self):
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict | None = None,
        limit: int | None = None,
        order: str | None = None,
        single: bool = False,
    ) -> list[dict] | dict | None:
        """查询记录"""
        url = f"{self.base_url}/{table}"
        params = {"select": columns}
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        if limit:
            self.headers["Range-Unit"] = "items"
            self.headers["Range"] = f"0-{limit - 1}"
        if order:
            params["order"] = order

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if single:
                    return data[0] if data else None
                return data
            elif resp.status_code == 404:
                return None if single else []
            else:
                raise Exception(f"Supabase error: {resp.status_code} {resp.text[:500]}")

    async def insert(self, table: str, data: dict | list[dict]) -> dict | list[dict]:
        """插入记录"""
        url = f"{self.base_url}/{table}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=data)
            if resp.status_code in (200, 201):
                return resp.json()
            raise Exception(f"Supabase insert error: {resp.status_code} {resp.text[:500]}")

    async def update(
        self, table: str, data: dict, filters: dict
    ) -> list[dict]:
        """更新记录"""
        url = f"{self.base_url}/{table}"
        params = {}
        for key, value in filters.items():
            params[key] = f"eq.{value}"

        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                url, headers=self.headers, json=data, params=params
            )
            if resp.status_code in (200, 204):
                return resp.json() if resp.text else []
            raise Exception(f"Supabase update error: {resp.status_code} {resp.text[:500]}")

    async def delete(self, table: str, filters: dict) -> int:
        """删除记录"""
        url = f"{self.base_url}/{table}"
        params = {}
        for key, value in filters.items():
            params[key] = f"eq.{value}"

        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=self.headers, params=params)
            if resp.status_code in (200, 204):
                return 1
            return 0

    async def rpc(self, function_name: str, params: dict | None = None) -> Any:
        """调用 PostgreSQL 函数"""
        url = f"{self.base_url}/rpc/{function_name}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, headers=self.headers, json=params or {}
            )
            if resp.status_code in (200, 201, 204):
                return resp.json() if resp.text else None
            raise Exception(f"Supabase RPC error: {resp.status_code} {resp.text[:500]}")


# 单例
supabase = SupabaseClient()
