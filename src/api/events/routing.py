import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import case, func
from timescaledb.hyperfunctions import time_bucket
from datetime import datetime, timedelta, timezone
from api.db.session import get_session
from api.db.config import DATABASE_URL

from .models import (
    EventModel, 
    EventBucketSchema, 
    EventCreateSchema,
    get_utc_now
)
router = APIRouter()

DEFAULT_LOOKUP_PAGES = [
        "/", "/about", "/pricing", "/contact", 
        "/blog", "/products", "/login", "/signup",
        "/dashboard", "/settings"
    ]

# Get data here
# List View
# GET /api/events/
@router.get("/", response_model=List[EventBucketSchema])
def read_events(
        duration: str = Query(default="1 day"),
        pages: List = Query(default=None),
        session: Session = Depends(get_session)
    ):
    # a bunch of items in a table
    os_case = case(
        (EventModel.user_agent.ilike('%windows%'), 'Windows'),
        (EventModel.user_agent.ilike('%macintosh%'), 'MacOS'),
        (EventModel.user_agent.ilike('%iphone%'), 'iOS'),
        (EventModel.user_agent.ilike('%android%'), 'Android'),
        (EventModel.user_agent.ilike('%linux%'), 'Linux'),
        else_='Other'
    ).label('operating_system')
    
    if DATABASE_URL.startswith("sqlite:///"):
        bucket = func.strftime("%Y-%m-%d", EventModel.time)
    else:
        bucket = time_bucket(duration, EventModel.time)
    # bucket = time_bucket(duration, EventModel.time)
    lookup_pages = pages if isinstance(pages, list) and len(pages) > 0 else DEFAULT_LOOKUP_PAGES
    query = (
        select(
            bucket.label('bucket'),
            os_case,
            EventModel.page.label('page'),
            func.avg(EventModel.duration).label("avg_duration"),
            func.count().label('count')
        )
        .where(
            EventModel.page.in_(lookup_pages)
        )
        .group_by(
            bucket,
            os_case,
            EventModel.page,
        )
        .order_by(
            bucket,
            os_case,
            EventModel.page,
        )
    )
    results = session.exec(query).fetchall()
    return results

# SEND DATA HERE
# create view
# POST /api/events/
@router.post("/", response_model=EventModel)
def create_event(
        payload:EventCreateSchema, 
        session: Session = Depends(get_session)):
    # a bunch of items in a table
    data = payload.model_dump() # payload -> dict -> pydantic
    obj = EventModel.model_validate(data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


# GET /api/events/12
@router.get("/{event_id}", response_model=EventModel)
def get_event(event_id:int, session: Session = Depends(get_session)):
    # a single row
    query = select(EventModel).where(EventModel.id == event_id)
    result = session.exec(query).first()
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


# @router.put("/{event_id}/", response_model=EventModel)
# def update_event_by_id(
#     event_id: int, payload: EventUpdateModel, session: Session = Depends(get_session)
# ):
#     query = select(EventModel).where(EventModel.id == event_id)
#     event = session.exec(query).first()
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     data = payload.model_dump()
#     for key, value in data.items():
#         if key == "id":
#             continue
#         setattr(event, key, value)
#     event.updated_at = datetime.now()
#     session.add(event)
#     session.commit()
#     session.refresh(event)
#     return event


# @router.delete("/{event_id}/", response_model=dict)
# def delete_event_by_id(event_id: int, session: Session = Depends(get_session)):
#     query = select(EventModel).where(EventModel.id == event_id)
#     event = session.exec(query).first()
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     session.delete(event)
#     session.commit()
#     return {"status": "success"}
