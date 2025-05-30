#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from concurrent.futures import ThreadPoolExecutor

import pytest
from common import (
    DATASET_NAME_LIMIT,
    INVALID_API_TOKEN,
    list_datasets,
    update_dataset,
)
from libs.auth import RAGFlowHttpApiAuth
from libs.utils import encode_avatar
from libs.utils.file_utils import create_image_file

# TODO: Missing scenario for updating embedding_model with chunk_count != 0


class TestAuthorization:
    @pytest.mark.parametrize(
        "auth, expected_code, expected_message",
        [
            (None, 0, "`Authorization` can't be empty"),
            (
                RAGFlowHttpApiAuth(INVALID_API_TOKEN),
                109,
                "Authentication error: API key is invalid!",
            ),
        ],
    )
    def test_invalid_auth(self, auth, expected_code, expected_message):
        res = update_dataset(auth, "dataset_id")
        assert res["code"] == expected_code
        assert res["message"] == expected_message


class TestDatasetUpdate:
    @pytest.mark.parametrize(
        "name, expected_code, expected_message",
        [
            ("valid_name", 0, ""),
            (
                "a" * (DATASET_NAME_LIMIT + 1),
                102,
                "Dataset name should not be longer than 128 characters.",
            ),
            (0, 100, """AttributeError("\'int\' object has no attribute \'strip\'")"""),
            (
                None,
                100,
                """AttributeError("\'NoneType\' object has no attribute \'strip\'")""",
            ),
            pytest.param("", 102, "", marks=pytest.mark.skip(reason="issue/5915")),
            ("dataset_1", 102, "Duplicated dataset name in updating dataset."),
            ("DATASET_1", 102, "Duplicated dataset name in updating dataset."),
        ],
    )
    def test_name(self, get_http_api_auth, add_datasets_func, name, expected_code, expected_message):
        dataset_ids = add_datasets_func
        res = update_dataset(get_http_api_auth, dataset_ids[0], {"name": name})
        assert res["code"] == expected_code
        if expected_code == 0:
            res = list_datasets(get_http_api_auth, {"id": dataset_ids[0]})
            assert res["data"][0]["name"] == name
        else:
            assert res["message"] == expected_message

    @pytest.mark.parametrize(
        "embedding_model, expected_code, expected_message",
        [
            ("BAAI/bge-large-zh-v1.5", 0, ""),
            ("maidalun1020/bce-embedding-base_v1", 0, ""),
            (
                "other_embedding_model",
                102,
                "`embedding_model` other_embedding_model doesn't exist",
            ),
            (None, 102, "`embedding_model` can't be empty"),
        ],
    )
    def test_embedding_model(self, get_http_api_auth, add_dataset_func, embedding_model, expected_code, expected_message):
        dataset_id = add_dataset_func
        res = update_dataset(get_http_api_auth, dataset_id, {"embedding_model": embedding_model})
        assert res["code"] == expected_code
        if expected_code == 0:
            res = list_datasets(get_http_api_auth, {"id": dataset_id})
            assert res["data"][0]["embedding_model"] == embedding_model
        else:
            assert res["message"] == expected_message

    @pytest.mark.parametrize(
        "chunk_method, expected_code, expected_message",
        [
            ("naive", 0, ""),
            ("manual", 0, ""),
            ("qa", 0, ""),
            ("table", 0, ""),
            ("paper", 0, ""),
            ("book", 0, ""),
            ("laws", 0, ""),
            ("presentation", 0, ""),
            ("picture", 0, ""),
            ("one", 0, ""),
            ("email", 0, ""),
            ("tag", 0, ""),
            ("", 0, ""),
            (
                "other_chunk_method",
                102,
                "'other_chunk_method' is not in ['naive', 'manual', 'qa', 'table', 'paper', 'book', 'laws', 'presentation', 'picture', 'one', 'email', 'tag']",
            ),
        ],
    )
    def test_chunk_method(self, get_http_api_auth, add_dataset_func, chunk_method, expected_code, expected_message):
        dataset_id = add_dataset_func
        res = update_dataset(get_http_api_auth, dataset_id, {"chunk_method": chunk_method})
        assert res["code"] == expected_code
        if expected_code == 0:
            res = list_datasets(get_http_api_auth, {"id": dataset_id})
            if chunk_method != "":
                assert res["data"][0]["chunk_method"] == chunk_method
            else:
                assert res["data"][0]["chunk_method"] == "naive"
        else:
            assert res["message"] == expected_message

    def test_avatar(self, get_http_api_auth, add_dataset_func, tmp_path):
        dataset_id = add_dataset_func
        fn = create_image_file(tmp_path / "ragflow_test.png")
        payload = {"avatar": encode_avatar(fn)}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 0

    def test_description(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func
        payload = {"description": "description"}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 0

        res = list_datasets(get_http_api_auth, {"id": dataset_id})
        assert res["data"][0]["description"] == "description"

    def test_pagerank(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func
        payload = {"pagerank": 1}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 0

        res = list_datasets(get_http_api_auth, {"id": dataset_id})
        assert res["data"][0]["pagerank"] == 1

    def test_similarity_threshold(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func
        payload = {"similarity_threshold": 1}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 0

        res = list_datasets(get_http_api_auth, {"id": dataset_id})
        assert res["data"][0]["similarity_threshold"] == 1

    @pytest.mark.parametrize(
        "permission, expected_code",
        [
            ("me", 0),
            ("team", 0),
            ("", 0),
            ("ME", 102),
            ("TEAM", 102),
            ("other_permission", 102),
        ],
    )
    def test_permission(self, get_http_api_auth, add_dataset_func, permission, expected_code):
        dataset_id = add_dataset_func
        payload = {"permission": permission}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == expected_code

        res = list_datasets(get_http_api_auth, {"id": dataset_id})
        if expected_code == 0 and permission != "":
            assert res["data"][0]["permission"] == permission
        if permission == "":
            assert res["data"][0]["permission"] == "me"

    def test_vector_similarity_weight(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func
        payload = {"vector_similarity_weight": 1}
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 0

        res = list_datasets(get_http_api_auth, {"id": dataset_id})
        assert res["data"][0]["vector_similarity_weight"] == 1

    def test_invalid_dataset_id(self, get_http_api_auth):
        res = update_dataset(get_http_api_auth, "invalid_dataset_id", {"name": "invalid_dataset_id"})
        assert res["code"] == 102
        assert res["message"] == "You don't own the dataset"

    @pytest.mark.parametrize(
        "payload",
        [
            {"chunk_count": 1},
            {"create_date": "Tue, 11 Mar 2025 13:37:23 GMT"},
            {"create_time": 1741671443322},
            {"created_by": "aa"},
            {"document_count": 1},
            {"id": "id"},
            {"status": "1"},
            {"tenant_id": "e57c1966f99211efb41e9e45646e0111"},
            {"token_num": 1},
            {"update_date": "Tue, 11 Mar 2025 13:37:23 GMT"},
            {"update_time": 1741671443339},
        ],
    )
    def test_modify_read_only_field(self, get_http_api_auth, add_dataset_func, payload):
        dataset_id = add_dataset_func
        res = update_dataset(get_http_api_auth, dataset_id, payload)
        assert res["code"] == 101
        assert "is readonly" in res["message"]

    def test_modify_unknown_field(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func
        res = update_dataset(get_http_api_auth, dataset_id, {"unknown_field": 0})
        assert res["code"] == 100

    @pytest.mark.slow
    def test_concurrent_update(self, get_http_api_auth, add_dataset_func):
        dataset_id = add_dataset_func

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_dataset, get_http_api_auth, dataset_id, {"name": f"dataset_{i}"}) for i in range(100)]
        responses = [f.result() for f in futures]
        assert all(r["code"] == 0 for r in responses)
