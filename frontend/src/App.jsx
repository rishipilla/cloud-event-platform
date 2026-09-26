import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import {
  Activity,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Server,
  XCircle,
  Zap,
  X,
  ChevronRight,
  Send,
} from "lucide-react";
import "./App.css";


const API_URL = "http://localhost:8030";

const POLL_INTERVAL_MS = 5000;


const CONSUMERS = [
  {
    key: "notification",
    name: "Notification",
    queue: "notification_queue",
  },
  {
    key: "analytics",
    name: "Analytics",
    queue: "analytics_queue",
  },
  {
    key: "audit",
    name: "Audit",
    queue: "audit_queue",
  },
];


const STATUS_META = {

  failed: {
    className: "status-failed",
    Icon: XCircle,
  },

  retrying: {
    className: "status-retrying",
    Icon: Clock3,
  },

  processing: {
    className: "status-processing",
    Icon: Activity,
  },

  published: {
    className: "status-published",
    Icon: Activity,
  },

  processed: {
    className: "status-completed",
    Icon: CheckCircle2,
  },

  completed: {
    className: "status-completed",
    Icon: CheckCircle2,
  },

};


const DEFAULT_STATUS_META =
  STATUS_META.completed;


function statusMeta(status) {

  return (
    STATUS_META[
      status?.toLowerCase()
    ] ??
    DEFAULT_STATUS_META
  );

}


const CONSUMER_ICON_META = {

  failed: {
    className: "detail-icon-failed",
    Icon: XCircle,
  },

  retrying: {
    className: "detail-icon-retrying",
    Icon: Clock3,
  },

};


const DEFAULT_CONSUMER_ICON_META = {

  className:
    "detail-icon-success",

  Icon: CheckCircle2,

};


function consumerIconMeta(status) {

  return (
    CONSUMER_ICON_META[
      status?.toLowerCase()
    ] ??
    DEFAULT_CONSUMER_ICON_META
  );

}


function formatDate(value) {

  return value
    ? new Date(value).toLocaleString()
    : "—";

}


function capitalize(value) {

  if (!value) {
    return "";
  }

  return (
    value.charAt(0).toUpperCase() +
    value.slice(1)
  );

}


function getConsumerStats(
  consumers,
  name
) {

  const consumer =
    consumers.find(
      (item) =>
        item.consumer === name
    );


  return {

    processed:
      consumer?.processed || 0,

    failed:
      consumer?.failed || 0,

    retrying:
      consumer?.retrying || 0,

  };

}


function getOverallEventStatus(
  event
) {

  const consumers =
    event.consumers || [];


  if (
    consumers.some(
      (consumer) =>
        consumer.status ===
        "failed"
    )
  ) {

    return "failed";

  }


  if (
    consumers.some(
      (consumer) =>
        consumer.status ===
        "retrying"
    )
  ) {

    return "retrying";

  }


  if (
    consumers.length >=
      CONSUMERS.length &&
    consumers.every(
      (consumer) =>
        consumer.status ===
        "processed"
    )
  ) {

    return "processed";

  }


  if (
    consumers.length > 0
  ) {

    return "processing";

  }


  return "published";

}


function App() {

  const [dashboard, setDashboard] =
    useState({

      total_events: 0,

      processed_events: 0,

      failed_events: 0,

      retrying_events: 0,

      consumers: [],

      recent_events: [],

    });


  const [loading, setLoading] =
    useState(true);


  const [refreshing, setRefreshing] =
    useState(false);


  const [selectedEvent, setSelectedEvent] =
    useState(null);


  const [loadingEvent, setLoadingEvent] =
    useState(false);


  const [showPublisher, setShowPublisher] =
    useState(false);


  const loadDashboard =
    useCallback(async () => {

      try {

        setRefreshing(true);


        const response =
          await axios.get(
            `${API_URL}/dashboard`
          );


        setDashboard(
          response.data
        );


      } catch (error) {

        console.error(
          "Failed to load dashboard:",
          error
        );


      } finally {

        setLoading(false);

        setRefreshing(false);

      }

    }, []);


  const openEventInspector =
    useCallback(
      async (eventId) => {

        try {

          setLoadingEvent(true);


          const response =
            await axios.get(
              `${API_URL}/events/${eventId}`
            );


          setSelectedEvent(
            response.data
          );


        } catch (error) {

          console.error(
            "Failed to load event:",
            error
          );


        } finally {

          setLoadingEvent(false);

        }

      },
      []
    );


  const closeEventInspector =
    useCallback(
      () =>
        setSelectedEvent(null),
      []
    );


  useEffect(() => {

    loadDashboard();


    const interval =
      setInterval(
        loadDashboard,
        POLL_INTERVAL_MS
      );


    return () =>
      clearInterval(interval);

  }, [loadDashboard]);


  useEffect(() => {

    if (!selectedEvent) {
      return;
    }


    const onKeyDown = (event) => {

      if (
        event.key === "Escape"
      ) {

        closeEventInspector();

      }

    };


    window.addEventListener(
      "keydown",
      onKeyDown
    );


    return () =>
      window.removeEventListener(
        "keydown",
        onKeyDown
      );

  }, [
    selectedEvent,
    closeEventInspector,
  ]);


  return (

    <div className="app">

      <header className="header">

        <div className="brand">

          <div className="brand-icon">

            <Zap size={20} />

          </div>


          <div>

            <h1>
              EventFlow
            </h1>

            <p>
              Event-Driven Processing Platform
            </p>

          </div>

        </div>


        <div className="header-actions">

          <button
            className="publish-button"
            onClick={() =>
              setShowPublisher(true)
            }
          >

            <Send size={16} />

            Publish Event

          </button>


          <button
            className="refresh-button"
            onClick={loadDashboard}
            disabled={refreshing}
          >

            <RefreshCw
              size={17}
              className={
                refreshing
                  ? "spin"
                  : ""
              }
            />

            Refresh

          </button>

        </div>

      </header>


      <section className="system-status">

        <div className="status-indicator">

          <span className="status-dot" />

          <span>
            Event system operational
          </span>

        </div>


        <div className="status-meta">

          <span>
            API
          </span>

          <strong>
            :8030
          </strong>

          <span>
            •
          </span>

          <span>
            RabbitMQ
          </span>

          <strong>
            Connected
          </strong>

        </div>

      </section>


      <section className="stats-grid">

        <StatCard
          title="Total Events"
          value={
            dashboard.total_events
          }
          icon={
            <Activity size={21} />
          }
          description="Events stored"
        />


        <StatCard
          title="Processed"
          value={
            dashboard.processed_events
          }
          icon={
            <CheckCircle2 size={21} />
          }
          description="All consumers completed"
        />


        <StatCard
          title="Failed"
          value={
            dashboard.failed_events
          }
          icon={
            <XCircle size={21} />
          }
          description="Consumer failures"
        />


        <StatCard
          title="Retrying"
          value={
            dashboard.retrying_events
          }
          icon={
            <Clock3 size={21} />
          }
          description="Automatic retries"
        />


        <StatCard
          title="Consumers"
          value={
            CONSUMERS.length
          }
          icon={
            <Server size={21} />
          }
          description="Active consumers"
        />

      </section>


      <section className="events-section card">

        <div className="section-header">

          <div>

            <h2>
              Recent Events
            </h2>

            <p>
              Click an event to inspect its processing details
            </p>

          </div>


          <div className="live-indicator">

            <span />

            Live

          </div>

        </div>


        <div className="table-wrapper">

          {loading ? (

            <div className="empty-state">

              Loading events...

            </div>

          ) : dashboard.recent_events.length === 0 ? (

            <div className="empty-state">

              No events available yet.

            </div>

          ) : (

            <table>

              <thead>

                <tr>

                  <th>
                    Event ID
                  </th>

                  <th>
                    Event Type
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Consumers
                  </th>

                  <th>
                    Created
                  </th>

                  <th
                    aria-hidden="true"
                  />

                </tr>

              </thead>


              <tbody>

                {dashboard.recent_events.map(
                  (event) => (

                    <tr
                      key={
                        event.event_id
                      }

                      className="event-row"

                      role="button"

                      tabIndex={0}

                      onClick={() =>
                        openEventInspector(
                          event.event_id
                        )
                      }

                      onKeyDown={(
                        keyEvent
                      ) => {

                        if (
                          keyEvent.key ===
                            "Enter" ||
                          keyEvent.key ===
                            " "
                        ) {

                          keyEvent.preventDefault();


                          openEventInspector(
                            event.event_id
                          );

                        }

                      }}
                    >

                      <td>

                        <span className="event-id">

                          {event.event_id.slice(
                            0,
                            8
                          )}

                        </span>

                      </td>


                      <td>

                        <span className="event-type">

                          {event.event_type}

                        </span>

                      </td>


                      <td>

                        <StatusBadge
                          status={
                            event.status
                          }
                        />

                      </td>


                      <td>

                        <span className="consumer-count">

                          {
                            event.processed_count
                          }

                          /

                          {CONSUMERS.length}

                        </span>

                      </td>


                      <td>

                        <span className="timestamp">

                          {formatDate(
                            event.created_at
                          )}

                        </span>

                      </td>


                      <td>

                        <ChevronRight
                          size={16}
                          className="event-arrow"
                        />

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          )}

        </div>

      </section>


      <section className="consumers-section card">

        <div className="section-header">

          <div>

            <h2>
              Consumers
            </h2>

            <p>
              Independent event processors
            </p>

          </div>

        </div>


        <div className="consumer-grid">

          {CONSUMERS.map(
            (consumer) => (

              <ConsumerCard
                key={
                  consumer.key
                }

                name={
                  consumer.name
                }

                queue={
                  consumer.queue
                }

                stats={
                  getConsumerStats(
                    dashboard.consumers,
                    consumer.key
                  )
                }

              />

            )
          )}

        </div>

      </section>


      {showPublisher && (

        <EventPublisher
          onClose={() =>
            setShowPublisher(false)
          }

          onPublished={() => {

            setShowPublisher(false);

            loadDashboard();

          }}

        />

      )}


      {loadingEvent && (

        <div
          className="modal-overlay"
          role="presentation"
        >

          <div className="event-modal loading-modal">

            Loading event details...

          </div>

        </div>

      )}


      {selectedEvent && (

        <EventInspector
          event={selectedEvent}
          onClose={
            closeEventInspector
          }
        />

      )}

    </div>

  );

}


/* =========================
   STAT CARD
========================= */

function StatCard({
  title,
  value,
  icon,
  description,
}) {

  return (

    <div className="stat-card card">

      <div className="stat-top">

        <div className="stat-icon">

          {icon}

        </div>


        <span className="stat-title">

          {title}

        </span>

      </div>


      <div className="stat-value">

        {value}

      </div>


      <div className="stat-description">

        {description}

      </div>

    </div>

  );

}


/* =========================
   STATUS BADGE
========================= */

function StatusBadge({
  status,
}) {

  const {
    className,
    Icon,
  } = statusMeta(status);


  return (

    <span
      className={
        `status-badge ${className}`
      }
    >

      <Icon size={14} />

      {status}

    </span>

  );

}


/* =========================
   CONSUMER CARD
========================= */

function ConsumerCard({
  name,
  queue,
  stats,
}) {

  return (

    <div className="consumer-card">

      <div className="consumer-icon">

        <Server size={20} />

      </div>


      <div className="consumer-info">

        <h3>
          {name}
        </h3>


        <p>
          {queue}
        </p>


        <div className="consumer-stats">

          <span>
            Processed: {stats.processed}
          </span>


          <span>
            Failed: {stats.failed}
          </span>


          <span>
            Retried: {stats.retrying}
          </span>

        </div>

      </div>


      <div className="consumer-status">

        <span />

        Running

      </div>

    </div>

  );

}


/* =========================
   EVENT PUBLISHER
========================= */

function EventPublisher({
  onClose,
  onPublished,
}) {

  const [eventType, setEventType] =
    useState(
      "order.created"
    );


  const [payload, setPayload] =
    useState(
      JSON.stringify(
        {
          order_id:
            "ORD-1002",

          customer:
            "customer-001",

          amount: 2500,
        },

        null,

        2
      )
    );


  const [publishing, setPublishing] =
    useState(false);


  const [error, setError] =
    useState("");


  const publishEvent =
    async () => {

      setError("");


      let parsedPayload;


      try {

        parsedPayload =
          JSON.parse(payload);

      } catch {

        setError(
          "Payload must contain valid JSON."
        );

        return;

      }


      if (
        !eventType.trim()
      ) {

        setError(
          "Event type is required."
        );

        return;

      }


      try {

        setPublishing(true);


        await axios.post(
          `${API_URL}/events`,
          {
            event_type:
              eventType.trim(),

            payload:
              parsedPayload,
          }
        );


        onPublished();


      } catch (error) {

        console.error(
          "Failed to publish event:",
          error
        );


        setError(
          error.response?.data?.detail ||
          "Failed to publish event."
        );


      } finally {

        setPublishing(false);

      }

    };


  return (

    <div
      className="modal-overlay"
      onClick={onClose}
      role="presentation"
    >

      <div
        className="event-modal publisher-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Publish event"
        onClick={(event) =>
          event.stopPropagation()
        }
      >

        <div className="modal-header">

          <div>

            <h2>
              Publish Event
            </h2>

            <p>
              Send a new event through RabbitMQ
            </p>

          </div>


          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close"
          >

            <X size={19} />

          </button>

        </div>


        <div className="modal-body">

          <div className="form-group">

            <label htmlFor="event-type">

              Event Type

            </label>


            <input
              id="event-type"
              className="event-input"
              type="text"
              value={eventType}
              onChange={(event) =>
                setEventType(
                  event.target.value
                )
              }
              placeholder="order.created"
            />

          </div>


          <div className="form-group">

            <label htmlFor="event-payload">

              Payload

            </label>


            <textarea
              id="event-payload"
              className="event-textarea"
              value={payload}
              onChange={(event) =>
                setPayload(
                  event.target.value
                )
              }
              spellCheck="false"
            />

          </div>


          {error && (

            <div className="publisher-error">

              {error}

            </div>

          )}


          <div className="publisher-actions">

            <button
              className="cancel-button"
              onClick={onClose}
              disabled={publishing}
            >

              Cancel

            </button>


            <button
              className="publish-submit-button"
              onClick={publishEvent}
              disabled={publishing}
            >

              <Send size={15} />

              {publishing
                ? "Publishing..."
                : "Publish Event"}

            </button>

          </div>

        </div>

      </div>

    </div>

  );

}


/* =========================
   EVENT INSPECTOR
========================= */

function EventInspector({
  event,
  onClose,
}) {

  const consumers =
    event.consumers ?? [];


  return (

    <div
      className="modal-overlay"
      onClick={onClose}
      role="presentation"
    >

      <div
        className="event-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Event inspector"
        onClick={(clickEvent) =>
          clickEvent.stopPropagation()
        }
      >

        <div className="modal-header">

          <div>

            <h2>
              Event Inspector
            </h2>

            <p>
              Detailed event processing information
            </p>

          </div>


          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close"
          >

            <X size={19} />

          </button>

        </div>


        <div className="modal-body">

          <div className="event-detail-top">

            <div>

              <span className="detail-label">

                Event Type

              </span>


              <div className="detail-value">

                {event.event_type}

              </div>

            </div>


            <StatusBadge
              status={
                getOverallEventStatus(
                  event
                )
              }
            />

          </div>


          <div className="detail-block">

            <span className="detail-label">

              Event ID

            </span>


            <div className="event-id-full">

              {event.event_id}

            </div>

          </div>


          <div className="detail-block">

            <span className="detail-label">

              Created

            </span>


            <div className="detail-value">

              {formatDate(
                event.created_at
              )}

            </div>

          </div>


          <div className="detail-block">

            <span className="detail-label">

              Payload

            </span>


            <pre className="payload-box">

              {JSON.stringify(
                event.payload,
                null,
                2
              )}

            </pre>

          </div>


          <div className="detail-block">

            <div className="consumer-detail-header">

              <span className="detail-label">

                Consumer Processing

              </span>


              <p>

                Independent processing results

              </p>

            </div>


            <div className="consumer-detail-list">

              {consumers.length === 0 ? (

                <div className="no-consumers">

                  No consumer records yet.

                </div>

              ) : (

                consumers.map(
                  (
                    consumer,
                    index
                  ) => (

                    <ConsumerDetail
                      key={
                        `${consumer.consumer}-${index}`
                      }
                      consumer={
                        consumer
                      }
                    />

                  )
                )

              )}

            </div>

          </div>

        </div>

      </div>

    </div>

  );

}


/* =========================
   CONSUMER DETAIL
========================= */

function ConsumerDetail({
  consumer,
}) {

  const {
    className,
    Icon,
  } =
    consumerIconMeta(
      consumer.status
    );


  return (

    <div className="consumer-detail">

      <div
        className={
          `consumer-detail-icon ${className}`
        }
      >

        <Icon size={17} />

      </div>


      <div className="consumer-detail-info">

        <div className="consumer-detail-name">

          {capitalize(
            consumer.consumer
          )}

        </div>


        <div className="consumer-detail-meta">

          Status:
          {" "}

          <strong>
            {consumer.status}
          </strong>

          {" • "}

          Attempts:
          {" "}

          <strong>
            {consumer.attempts}
          </strong>

        </div>


        {consumer.error && (

          <div className="consumer-error">

            {consumer.error}

          </div>

        )}


        {consumer.processed_at && (

          <div className="consumer-processed-time">

            Processed:
            {" "}

            {formatDate(
              consumer.processed_at
            )}

          </div>

        )}

      </div>

    </div>

  );

}


export default App;