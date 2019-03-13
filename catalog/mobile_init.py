from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from mobile_dbsetup import *
engine = create_engine('sqlite:///Mobile.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
session.query(MobileStore).delete()
session.query(MobileVersions).delete()
session.query(User).delete()
SampleUser = User(
    name="Nandini Muppalla",
    email="nandinimmuppalla@gmail.com")
session.add(SampleUser)
session.commit()
print("done to add")
MobileStore1 = MobileStore(
    name="SAMSUNG", user_id=1)
session.add(MobileStore1)
session.commit()
MobileStore2 = MobileStore(
    name="VIVO", user_id=1)
session.add(MobileStore2)
session.commit()
print("add successfull")
Mobile1 = MobileVersions(
                       name="j10",
                       price="5550",
                       edition="2019",
                       specifications="32GBstorage,2GB RAM",
                       color="white",
                       rating="good",
                       mobilestoreid=1,
                       user_id=1)
session.add(Mobile1)
session.commit()
Mobile2 = MobileVersions(
                       name="y7",
                       price="6550",
                       edition="2019",
                       specifications="32GBstorage,2GB RAM",
                       color="black",
                       rating="good",
                       mobilestoreid=1,
                       user_id=1)
session.add(Mobile2)
session.commit()
print("data  inserted successfully!")
