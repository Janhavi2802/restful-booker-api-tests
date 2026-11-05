# SoapUI: mirrored Restful-Booker scenarios

Build this project in SoapUI (open source, 5.7+) and save it here as
`soapui/Restful-Booker-soapui-project.xml`. Building it yourself takes about
an hour, and you will be able to explain every step in an interview.

## 1. Create the project

1. **File → New REST Project**, URI: `https://restful-booker.herokuapp.com`
2. Rename the project to `Restful-Booker`.
3. Add resources: `/auth`, `/booking`, `/booking/{id}`, `/ping`.
4. On the project, add a **custom property** `baseUrl` and a test-suite
   property `token` (filled in at runtime).

## 2. Test suite: `Booking API`

### Test case 1: `Auth - valid login`

| Step | Type | Details |
| --- | --- | --- |
| Create token | REST request | `POST /auth`, body `{"username":"admin","password":"password123"}`, header `Content-Type: application/json` |
| Assertions | | **Valid HTTP Status Codes** `200`; **JsonPath Existence Match** `$.token` = true |
| Save token | Property Transfer | Source: response `$.token` → Target: test-suite property `token` |

### Test case 2: `Booking CRUD`

| Step | Request | Assertions |
| --- | --- | --- |
| Create booking | `POST /booking` with the booking JSON | Status `200`; JsonPath Match `$.booking.firstname` = `${#TestCase#firstname}` |
| Transfer id | Property Transfer `$.bookingid` → test-case property `bookingId` | |
| Get booking | `GET /booking/${#TestCase#bookingId}` | Status `200`; JsonPath Match `$.lastname` |
| Update booking | `PUT /booking/${#TestCase#bookingId}`, header `Cookie: token=${#TestSuite#token}` | Status `200`; JsonPath Match `$.firstname` = `Updated` |
| Delete booking | `DELETE /booking/${#TestCase#bookingId}` with the same Cookie header | Status `201` |
| Verify deleted | `GET /booking/${#TestCase#bookingId}` | Status `404` |

### Test case 3: `Negative - auth and errors`

| Step | Request | Assertion |
| --- | --- | --- |
| Bad login | `POST /auth` with a wrong password | Status `200`; Contains `Bad credentials` |
| Update without token | `PUT /booking/1`, no Cookie header | Status `403` |
| Invalid token | `PUT /booking/1`, `Cookie: token=invalid123` | Status `403` |
| Missing field | `POST /booking` without `firstname` | Status `500` (documents a real defect: should be 400) |
| Unknown id | `GET /booking/999999999` | Status `404` |

## 3. Data-driven test steps

SoapUI open source has no DataSource step (that's in ReadyAPI), so use a
**Groovy Script** loop over `data/bookings.json` from this repo:

```groovy
import groovy.json.JsonSlurper

def dataFile = new File(context.expand('${projectDir}') + '/../data/bookings.json')
def cases = new JsonSlurper().parse(dataFile)
def idx = (context.getProperty('rowIndex') ?: 0) as int

if (idx < cases.size()) {
    def p = cases[idx].payload
    testRunner.testCase.setPropertyValue('firstname', p.firstname)
    testRunner.testCase.setPropertyValue('lastname', p.lastname)
    testRunner.testCase.setPropertyValue('totalprice', p.totalprice.toString())
    context.setProperty('rowIndex', idx + 1)
} else {
    testRunner.gotoStepByName('End')   // a Delay step named End, or any final step
}
```

Put this script first, the `Create booking` request (using
`${#TestCase#firstname}` etc. in its body) second, and a **Conditional Goto**
or second Groovy step that jumps back to the script until all rows are used.

## 4. Run from the command line

```bash
<SoapUI>/bin/testrunner.sh -sBooking\ API -r -j -f soapui-reports soapui/Restful-Booker-soapui-project.xml
```

`-j` writes JUnit XML that Jenkins or GitHub Actions can publish.
