from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy import create_engine
import os # NOVO

Base = declarative_base()

class Pasta(Base):
    __tablename__ = "pastas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    produtos = relationship("Produto", back_populates="pasta")

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String(13), nullable=True)
    plu = Column(String(5), nullable=True)
    nome = Column(String, nullable=False)
    quantidade = Column(Integer, default=0)
    data_validade = Column(String, nullable=True)
    is_shared = Column(Boolean, default=False, nullable=False)
    pasta_id = Column(Integer, ForeignKey("pastas.id"), nullable=True)
    pasta = relationship("Pasta", back_populates="produtos")

# --- Conexão com o banco ---

# MODIFICADO: Caminho para o banco de dados na pasta 'data'
DB_PATH = os.path.join("data", "projeto2.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)