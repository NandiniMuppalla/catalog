import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)


class MobileStore(Base):
    __tablename__ = 'mobilestore'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="mobilestore")

    @property
    def serialize(self):
        """Return object data in easily serializable format """
        return{
                'name': self. name,
                'id': self.id
            }


class MobileVersions(Base):
    __tablename__ = 'mobile_versions'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    price = Column(String(8))
    edition = Column(String(250))
    specifications = Column(String(500))
    color = Column(String(250))
    rating = Column(String(200))
    mobilestoreid = Column(Integer, ForeignKey('mobilestore.id'))
    mobilestore = relationship(
        MobileStore, backref=backref('mobile_versions', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="mobile_versions")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self. name,
            'price': self. price,
            'edition': self. edition,
            'specifictaions': self. specifications,
            'color': self.color,
            'rating': self. rating,
            'id': self. id
        }
engin = create_engine('sqlite:///Mobile.db')
Base.metadata.create_all(engin)
