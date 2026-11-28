import unittest
from types import SimpleNamespace
from scripts.kaggle_kernel_absence_guard import KNOWN, verify_absent

TARGET="kolihhan/gemma4-core6-structural-paired-20261129-v1"
class Fake:
    def __init__(self):
        self.candidate=[]
        self.control=[SimpleNamespace(ref=KNOWN)]
        self.token=None
        self.status_exists=False
        self.error=ValueError(f"Cannot access kernel '{TARGET}' (Permission 'kernels.get' was denied).")
    def kernels_list_with_response(self,*,mine,search,page,page_size):
        assert mine and page==1 and page_size==100
        return SimpleNamespace(kernels=self.control if search==KNOWN.split("/")[1] else self.candidate,next_page_token=self.token)
    def kernels_status(self,target):
        if target==KNOWN or self.status_exists:return SimpleNamespace(status="KernelWorkerStatus.COMPLETE")
        raise self.error

class GuardTests(unittest.TestCase):
    def test_empty_structured_listing(self):
        self.assertTrue(verify_absent(Fake(),TARGET)["positive_control"])
    def test_existing_status(self):
        a=Fake();a.status_exists=True
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
    def test_existing_listing(self):
        a=Fake();a.candidate=[SimpleNamespace(ref=TARGET)]
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
    def test_unexpected_error(self):
        a=Fake();a.error=ValueError("unrelated failure")
        with self.assertRaises(ValueError):verify_absent(a,TARGET)
    def test_pagination(self):
        a=Fake();a.token="next"
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
    def test_bad_positive_control(self):
        a=Fake();a.control=[]
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
    def test_malformed(self):
        a=Fake();a.candidate=[None]
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
    def test_none_listing(self):
        a=Fake();a.candidate=None
        with self.assertRaises(RuntimeError):verify_absent(a,TARGET)
if __name__=="__main__":unittest.main()
