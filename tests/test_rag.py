import pytest
from emporio_agent.rag.retriever import PolicyRetriever


@pytest.fixture
def retriever():
    return PolicyRetriever()


def test_retrieve_store_hours(retriever):
    chunks = retriever.retrieve("qual o horário de atendimento no sábado e domingo?", top_k=2)
    assert len(chunks) > 0
    top = chunks[0]
    assert "horário" in top.title.lower() or "funcionamento" in top.title.lower()
    assert "09:00" in top.content or "sábado" in top.content.lower()


def test_retrieve_return_policy(retriever):
    chunks = retriever.retrieve("me arrependi da compra, posso devolver?", top_k=2)
    assert len(chunks) > 0
    contents = " ".join([c.content for c in chunks])
    assert "arrependimento" in contents.lower() or "troca" in contents.lower()
    assert "7" in contents or "sete" in contents.lower()


def test_retrieve_store_address(retriever):
    chunks = retriever.retrieve("qual o endereço da loja e telefone?", top_k=2)
    assert len(chunks) > 0
    contents = " ".join([c.content for c in chunks])
    assert "14 de maio" in contents.lower() or "campo grande" in contents.lower()


def test_retrieve_scope_and_accessories(retriever):
    chunks = retriever.retrieve("vocês vendem cordas, palhetas e amplificadores?", top_k=2)
    assert len(chunks) > 0
    contents = " ".join([c.content for c in chunks])
    assert "exclusivamente" in contents.lower() or "acessórios" in contents.lower() or "não comercializamos" in contents.lower()
