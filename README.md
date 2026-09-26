\# Cloud Event-Driven Processing Platform



A containerized event-driven processing platform built with FastAPI, RabbitMQ, PostgreSQL, Python workers, and React.



The platform demonstrates how a single event can be published once and independently consumed by multiple services using a RabbitMQ fanout exchange.



\---



\## Overview



Traditional request-based systems often tightly couple services together.



This project demonstrates an event-driven architecture where:



1\. A client publishes an event.

2\. The API stores the event in PostgreSQL.

3\. RabbitMQ distributes the event through a fanout exchange.

4\. Multiple independent consumers receive the same event.

5\. Each consumer processes the event independently.

6\. Processing results are recorded in PostgreSQL.

7\. The React dashboard displays the event and consumer status.



This architecture makes it possible to add new consumers without changing the event publisher.



\---



\## Architecture



```text

&#x20;                   React Dashboard

&#x20;                          |

&#x20;                          | POST /events

&#x20;                          v

&#x20;                   +-------------+

&#x20;                   |   FastAPI   |

&#x20;                   |     API     |

&#x20;                   +------+------+

&#x20;                          |

&#x20;               +----------+----------+

&#x20;               |                     |

&#x20;               v                     v

&#x20;       +---------------+     +----------------+

&#x20;       |  PostgreSQL   |     |    RabbitMQ    |

&#x20;       | Event Storage |     | Fanout Exchange|

&#x20;       +---------------+     +-------+--------+

&#x20;                                     |

&#x20;                      +--------------+--------------+

&#x20;                      |              |              |

&#x20;                      v              v              v

&#x20;               +-------------+ +-------------+ +-------------+

&#x20;               | Notification| |  Analytics  | |    Audit    |

&#x20;               |   Worker    | |   Worker    | |   Worker    |

&#x20;               +------+------+ +------+------+ +------+------+

&#x20;                      |              |              |

&#x20;                      +--------------+--------------+

&#x20;                                     |

&#x20;                                     v

&#x20;                              +-------------+

&#x20;                              | PostgreSQL  |

&#x20;                              | Consumption |

&#x20;                              |   Records   |

&#x20;                              +-------------+

